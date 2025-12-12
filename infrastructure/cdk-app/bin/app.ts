#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { PersonalAssistantStack } from '../lib/personal-assistant-stack';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config({ path: '../../.env' });

const app = new cdk.App();

new PersonalAssistantStack(app, 'PersonalAssistantStack', {
  env: {
    account: process.env.AWS_ACCOUNT_ID || process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.AWS_REGION || process.env.CDK_DEFAULT_REGION || 'eu-west-1',
  },
  description: 'Personal Assistant Suite with AWS Agent Core, Lambda, DynamoDB, and Telegram Bot',
  tags: {
    Project: 'PersonalAssistant',
    Environment: 'Production',
    ManagedBy: 'CDK'
  }
});
