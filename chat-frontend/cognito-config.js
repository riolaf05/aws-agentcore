/**
 * AWS Cognito Configuration
 * 
 * IMPORTANTE: Aggiorna questi valori dopo il deploy CDK
 * Esegui: cd infrastructure/cdk-app && cdk deploy
 * 
 * Copia gli output:
 * - UserPoolId
 * - UserPoolClientId
 * - IdentityPoolId
 */

// Funzione per aggiornare la configurazione Cognito
function updateCognitoConfig(userPoolId, clientId, region = 'us-east-1') {
    if (CONFIG) {
        CONFIG.COGNITO_USER_POOL_ID = userPoolId;
        CONFIG.COGNITO_CLIENT_ID = clientId;
        CONFIG.COGNITO_REGION = region;
        
        // Reinizializza il User Pool
        if (typeof AmazonCognitoIdentity !== 'undefined') {
            const poolData = {
                UserPoolId: userPoolId,
                ClientId: clientId
            };
            userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
            console.log('✅ Cognito configurato con successo');
        }
    }
}

// Esempio di utilizzo dopo il deploy:
// updateCognitoConfig('us-east-1_XXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXXXXX');
