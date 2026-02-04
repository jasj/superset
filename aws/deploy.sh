#!/bin/bash
# =============================================================================
# Superset AWS ECS Fargate Deployment Script
# =============================================================================

set -e

export PATH="$HOME/bin:$PATH"

# Configuration
AWS_REGION="us-east-1"
ECR_REPO="084828580816.dkr.ecr.us-east-1.amazonaws.com/superset"
ECS_CLUSTER="superset-cluster"
IMAGE_TAG="${1:-latest}"

echo "=========================================="
echo "Deploying Superset to AWS ECS Fargate"
echo "=========================================="
echo "Region: $AWS_REGION"
echo "Image: $ECR_REPO:$IMAGE_TAG"
echo ""

# Step 1: Login to ECR
echo "Step 1: Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO

# Step 2: Build and push Docker image
echo "Step 2: Building Docker image..."
docker build --platform linux/amd64 --target lean \
    -t $ECR_REPO:$IMAGE_TAG \
    -t $ECR_REPO:latest \
    .

echo "Step 3: Pushing Docker image to ECR..."
docker push $ECR_REPO:$IMAGE_TAG
docker push $ECR_REPO:latest

# Step 4: Register Task Definitions
echo "Step 4: Registering Task Definitions..."
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json --region $AWS_REGION
aws ecs register-task-definition --cli-input-json file://aws/task-definition-worker.json --region $AWS_REGION

# Step 5: Update or Create ECS Services
echo "Step 5: Updating ECS Services..."

# Check if superset service exists
if aws ecs describe-services --cluster $ECS_CLUSTER --services superset --region $AWS_REGION | grep -q "ACTIVE"; then
    echo "Updating existing superset service..."
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service superset \
        --task-definition superset \
        --force-new-deployment \
        --region $AWS_REGION
else
    echo "Creating superset service..."
    aws ecs create-service \
        --cluster $ECS_CLUSTER \
        --service-name superset \
        --task-definition superset \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[subnet-0cb922541b3eee478,subnet-04fc193960f482bf8],securityGroups=[sg-0f44a4c3e9c33dec9],assignPublicIp=ENABLED}" \
        --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:084828580816:targetgroup/superset-tg/3609d3c31dc732d9,containerName=superset,containerPort=8088" \
        --region $AWS_REGION
fi

# Check if worker service exists
if aws ecs describe-services --cluster $ECS_CLUSTER --services superset-worker --region $AWS_REGION | grep -q "ACTIVE"; then
    echo "Updating existing superset-worker service..."
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service superset-worker \
        --task-definition superset-worker \
        --force-new-deployment \
        --region $AWS_REGION
else
    echo "Creating superset-worker service..."
    aws ecs create-service \
        --cluster $ECS_CLUSTER \
        --service-name superset-worker \
        --task-definition superset-worker \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[subnet-0cb922541b3eee478,subnet-04fc193960f482bf8],securityGroups=[sg-0f44a4c3e9c33dec9],assignPublicIp=ENABLED}" \
        --region $AWS_REGION
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "ALB URL: https://superset-alb-1417417845.us-east-1.elb.amazonaws.com"
echo "Custom Domain: https://bi.sibuerp.dev (after DNS configuration)"
echo ""
echo "To configure DNS in GoDaddy:"
echo "  1. Go to GoDaddy DNS Management for sibuerp.dev"
echo "  2. Add a CNAME record:"
echo "     - Name: bi"
echo "     - Value: superset-alb-1417417845.us-east-1.elb.amazonaws.com"
echo "     - TTL: 600"
echo ""
