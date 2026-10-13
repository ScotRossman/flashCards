terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "my-flashcard-tfstate-bucket" 
    key            = "flashcard-app/terraform.tfstate"
    region         = "us-east-1"                   
    encrypt        = true
  }
}

provider "aws" {
  region = "us-east-1"
  profile = "default"
}

# 2. Package the Python App 
# This packages the entire /src folder so your relative imports match up
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/flashcardApp"
  output_path = "${path.module}/lambda_function.zip"
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

# 4. Deploy the Python Lambda Function
resource "aws_lambda_function" "flashcard_backend" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "math-flashcard-api-backend"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler" # Looks for main.py -> lambda_handler()
  runtime          = "python3.11"
  timeout          = 15
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}

# 5. Create the HTTP API Gateway (Cost-effective & simple for developers)
resource "aws_apigatewayv2_api" "http_api" {
  name          = "math-flashcard-http-api"
  protocol_type = "HTTP"
  
  # Crucial for future frontend integration: allows your local UI/Webapp to call this API without CORS errors
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["content-type"]
  }
}

# 6. Connect API Gateway to your Lambda function
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.flashcard_backend.arn
}

# 7. Create a Route (The actual URL pathway)
# Any GET or POST request to your URL ending in /flashcard will route to Python
resource "aws_apigatewayv2_route" "api_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "ANY /flashcard"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
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