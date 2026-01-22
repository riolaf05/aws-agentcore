#!/usr/bin/env node
"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
require("source-map-support/register");
const cdk = __importStar(require("aws-cdk-lib"));
const personal_assistant_stack_1 = require("../lib/personal-assistant-stack");
const dotenv = __importStar(require("dotenv"));
// Load environment variables
dotenv.config({ path: '../../.env' });
const app = new cdk.App();
new personal_assistant_stack_1.PersonalAssistantStack(app, 'PersonalAssistantStack', {
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
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiYXBwLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiYXBwLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBQ0EsdUNBQXFDO0FBQ3JDLGlEQUFtQztBQUNuQyw4RUFBeUU7QUFDekUsK0NBQWlDO0FBRWpDLDZCQUE2QjtBQUM3QixNQUFNLENBQUMsTUFBTSxDQUFDLEVBQUUsSUFBSSxFQUFFLFlBQVksRUFBRSxDQUFDLENBQUM7QUFFdEMsTUFBTSxHQUFHLEdBQUcsSUFBSSxHQUFHLENBQUMsR0FBRyxFQUFFLENBQUM7QUFFMUIsSUFBSSxpREFBc0IsQ0FBQyxHQUFHLEVBQUUsd0JBQXdCLEVBQUU7SUFDeEQsR0FBRyxFQUFFO1FBQ0gsT0FBTyxFQUFFLE9BQU8sQ0FBQyxHQUFHLENBQUMsY0FBYyxJQUFJLE9BQU8sQ0FBQyxHQUFHLENBQUMsbUJBQW1CO1FBQ3RFLE1BQU0sRUFBRSxPQUFPLENBQUMsR0FBRyxDQUFDLFVBQVUsSUFBSSxPQUFPLENBQUMsR0FBRyxDQUFDLGtCQUFrQixJQUFJLFdBQVc7S0FDaEY7SUFDRCxXQUFXLEVBQUUsa0ZBQWtGO0lBQy9GLElBQUksRUFBRTtRQUNKLE9BQU8sRUFBRSxtQkFBbUI7UUFDNUIsV0FBVyxFQUFFLFlBQVk7UUFDekIsU0FBUyxFQUFFLEtBQUs7S0FDakI7Q0FDRixDQUFDLENBQUMiLCJzb3VyY2VzQ29udGVudCI6WyIjIS91c3IvYmluL2VudiBub2RlXHJcbmltcG9ydCAnc291cmNlLW1hcC1zdXBwb3J0L3JlZ2lzdGVyJztcclxuaW1wb3J0ICogYXMgY2RrIGZyb20gJ2F3cy1jZGstbGliJztcclxuaW1wb3J0IHsgUGVyc29uYWxBc3Npc3RhbnRTdGFjayB9IGZyb20gJy4uL2xpYi9wZXJzb25hbC1hc3Npc3RhbnQtc3RhY2snO1xyXG5pbXBvcnQgKiBhcyBkb3RlbnYgZnJvbSAnZG90ZW52JztcclxuXHJcbi8vIExvYWQgZW52aXJvbm1lbnQgdmFyaWFibGVzXHJcbmRvdGVudi5jb25maWcoeyBwYXRoOiAnLi4vLi4vLmVudicgfSk7XHJcblxyXG5jb25zdCBhcHAgPSBuZXcgY2RrLkFwcCgpO1xyXG5cclxubmV3IFBlcnNvbmFsQXNzaXN0YW50U3RhY2soYXBwLCAnUGVyc29uYWxBc3Npc3RhbnRTdGFjaycsIHtcclxuICBlbnY6IHtcclxuICAgIGFjY291bnQ6IHByb2Nlc3MuZW52LkFXU19BQ0NPVU5UX0lEIHx8IHByb2Nlc3MuZW52LkNES19ERUZBVUxUX0FDQ09VTlQsXHJcbiAgICByZWdpb246IHByb2Nlc3MuZW52LkFXU19SRUdJT04gfHwgcHJvY2Vzcy5lbnYuQ0RLX0RFRkFVTFRfUkVHSU9OIHx8ICdldS13ZXN0LTEnLFxyXG4gIH0sXHJcbiAgZGVzY3JpcHRpb246ICdQZXJzb25hbCBBc3Npc3RhbnQgU3VpdGUgd2l0aCBBV1MgQWdlbnQgQ29yZSwgTGFtYmRhLCBEeW5hbW9EQiwgYW5kIFRlbGVncmFtIEJvdCcsXHJcbiAgdGFnczoge1xyXG4gICAgUHJvamVjdDogJ1BlcnNvbmFsQXNzaXN0YW50JyxcclxuICAgIEVudmlyb25tZW50OiAnUHJvZHVjdGlvbicsXHJcbiAgICBNYW5hZ2VkQnk6ICdDREsnXHJcbiAgfVxyXG59KTtcclxuIl19