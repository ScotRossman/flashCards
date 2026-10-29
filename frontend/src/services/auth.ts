import { Amplify } from 'aws-amplify'
import {
  fetchAuthSession,
  getCurrentUser,
  signInWithRedirect,
  signOut,
} from 'aws-amplify/auth'
import { cognitoUserPoolsTokenProvider } from 'aws-amplify/auth/cognito'
import { CookieStorage } from 'aws-amplify/utils'

const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID
const appClientId = import.meta.env.VITE_COGNITO_APP_CLIENT_ID
const cognitoDomain = import.meta.env.VITE_COGNITO_DOMAIN

const missingAuthSettings = [
  !userPoolId && 'VITE_COGNITO_USER_POOL_ID',
  !appClientId && 'VITE_COGNITO_APP_CLIENT_ID',
  !cognitoDomain && 'VITE_COGNITO_DOMAIN',
].filter((setting): setting is string => Boolean(setting))

export const authConfigurationError = missingAuthSettings.length
  ? `Cognito sign-in is not configured. Set ${missingAuthSettings.join(', ')} in frontend/.env.local.`
  : null

export const isCognitoConfigured = authConfigurationError === null

export type SignedInUser = Awaited<ReturnType<typeof getCurrentUser>>

export function configureCognitoAuth() {
  if (!userPoolId || !appClientId || !cognitoDomain) {
    return
  }

  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId: appClientId,
        loginWith: {
          oauth: {
            domain: cognitoDomain,
            scopes: ['openid', 'email', 'profile'],
            redirectSignIn: [window.location.origin],
            redirectSignOut: [window.location.origin],
            responseType: 'code',
          },
        },
      },
    },
  })

  cognitoUserPoolsTokenProvider.setKeyValueStorage(
    new CookieStorage({
      path: '/',
      sameSite: 'lax',
      secure: window.location.protocol === 'https:',
      expires: 1,
    }),
  )
}

export function startSignIn() {
  return signInWithRedirect()
}

export async function startSignOut() {
  if (!appClientId || !cognitoDomain) {
    throw new Error(authConfigurationError ?? 'Cognito sign-out is not configured.')
  }

  await signOut()

  const logoutUrl = new URL('/logout', `https://${cognitoDomain}`)
  logoutUrl.searchParams.set('client_id', appClientId)
  logoutUrl.searchParams.set('logout_uri', window.location.origin)
  window.location.assign(logoutUrl.toString())
}

export async function getIdentityToken() {
  if (!isCognitoConfigured) {
    throw new Error(authConfigurationError ?? 'Cognito sign-in is not configured.')
  }

  const session = await fetchAuthSession()
  const identityToken = session.tokens?.idToken?.toString()
  if (!identityToken) {
    throw new Error('Sign in before making an authorized API request.')
  }

  return identityToken
}
