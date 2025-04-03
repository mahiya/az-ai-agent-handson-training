RESOURCE_GROUP=""
APP_PLAN_NAME=""
WEB_APP_NAME=""
WEB_APP_REGION="japaneast"
WEB_APP_SKU="B1"
WEB_APP_RUNTIME="PYTHON:3.11"

az webapp up \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_PLAN_NAME \
    --name $WEB_APP_NAME \
    --location $WEB_APP_REGION \
    --sku $WEB_APP_SKU \
    --runtime $WEB_APP_RUNTIME

echo "Please access to:" https://$WEB_APP_NAME.azurewebsites.net/