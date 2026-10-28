terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket  = "my-flashcard-tfstate-bucket"
    key     = "flashcard-app/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = "us-east-1"
}

# 2. Package the Python App 
# This packages the entire /src folder so your relative imports match up
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-package"
  output_path = "${path.module}/lambda_function.zip"
}

variable "db_secret_arn" {
  description = "Secrets Manager ARN containing JSON keys username and password for the flashcards MySQL user."
  type        = string
}

variable "lambda_subnet_ids" {
  description = "Subnet IDs in the RDS VPC for the Lambda function and Secrets Manager endpoint."
  type        = list(string)
}

variable "rds_security_group_id" {
  description = "RDS security group ID that should allow MySQL access from the Lambda security group."
  type        = string
}

variable "cognito_user_pool_id" {
  description = "Cognito user pool ID used to authenticate React users."
  type        = string
}

variable "cognito_app_client_id" {
  description = "Public Cognito app client ID used by the React application."
  type        = string
}

data "aws_region" "current" {}

data "aws_security_group" "rds" {
  id = var.rds_security_group_id
}

resource "aws_security_group" "lambda" {
  name        = "math-flashcard-lambda"
  description = "Outbound access for the math flashcard Lambda."
  vpc_id      = data.aws_security_group.rds.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "secrets_manager_endpoint" {
  name        = "math-flashcard-secrets-manager-endpoint"
  description = "HTTPS access from the math flashcard Lambda to Secrets Manager."
  vpc_id      = data.aws_security_group.rds.vpc_id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_vpc_endpoint" "secrets_manager" {
  vpc_id              = data.aws_security_group.rds.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.lambda_subnet_ids
  security_group_ids  = [aws_security_group.secrets_manager_endpoint.id]
  private_dns_enabled = true
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_lambda" {
  security_group_id            = var.rds_security_group_id
  referenced_security_group_id = aws_security_group.lambda.id
  description                  = "Allow MySQL access from the math flashcard Lambda."
  ip_protocol                  = "tcp"
  from_port                    = 3306
  to_port                      = 3306
}

# 3. Security (IAM Role & Policy) for Lambda Execution
resource "aws_iam_role" "lambda_role" {
  name = "math_flashcard_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Attaches core logging permissions so you can view python print statements in CloudWatch
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_database_secret" {
  name = "read-flashcards-database-secret"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = var.db_secret_arn
    }]
  })
}

# 4. Deploy the Python Lambda Function
resource "aws_lambda_function" "flashcard_backend" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "math-flashcard-api-backend"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler" # Looks for main.py -> lambda_handler()
  runtime          = "python3.11"
  timeout          = 15
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      DB_HOST       = "flashcard-1.c47iysguc25a.us-east-1.rds.amazonaws.com"
      DB_PORT       = "3306"
      DB_NAME       = "flashcards"
      DB_SECRET_ARN = var.db_secret_arn
    }
  }

  vpc_config {
    subnet_ids         = var.lambda_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
}

# 5. Create the HTTP API Gateway (Cost-effective & simple for developers)
resource "aws_apigatewayv2_api" "http_api" {
  name          = "math-flashcard-http-api"
  protocol_type = "HTTP"

  # Crucial for future frontend integration: allows your local UI/Webapp to call this API without CORS errors
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = [
      "authorization",
      "content-type",
      "x-amz-date",
      "x-amz-security-token",
      "x-amz-content-sha256",
    ]
  }
}

# 6. Connect API Gateway to your Lambda function
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.flashcard_backend.arn
}

resource "aws_apigatewayv2_authorizer" "jwt_authorizer" {
  api_id           = aws_apigatewayv2_api.http_api.id
  name             = "flashcard-cognito-jwt"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = [var.cognito_app_client_id]
    issuer   = "https://cognito-idp.${data.aws_region.current.name}.amazonaws.com/${var.cognito_user_pool_id}"
  }
}

# 7. Keep question retrieval public and require Cognito JWT authorization for writes.
resource "aws_apigatewayv2_route" "get_api_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /flashcard"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "react_player_api_route" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "POST /flashcard"
  target             = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt_authorizer.id
}

resource "aws_apigatewayv2_route" "streamlit_player_api_route" {
  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = "POST /streamlit/flashcard"
  target             = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
  authorization_type = "AWS_IAM"
}

# 8. Deploy the API Live
resource "aws_apigatewayv2_stage" "api_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default" # Automatically makes it available right away
  auto_deploy = true
}

# 9. Give API Gateway Permission to run your Lambda function
resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.flashcard_backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# 10. Output the final live URL string into your terminal when done!
output "base_url" {
  value       = "${aws_apigatewayv2_api.http_api.api_endpoint}/flashcard"
  description = "The public web URL for your math flashcard backend."
}

output "react_player_api_invoke_arn" {
  value       = "${aws_apigatewayv2_api.http_api.execution_arn}/$default/POST/flashcard"
  description = "Invocation ARN for React's POST route; it requires a valid Cognito JWT."
}

output "streamlit_player_api_invoke_arn" {
  value       = "${aws_apigatewayv2_api.http_api.execution_arn}/$default/POST/streamlit/flashcard"
  description = "Grant execute-api:Invoke on this ARN to the Streamlit IAM identity."
}