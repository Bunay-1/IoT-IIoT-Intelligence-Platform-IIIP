def register_customer(customer_data):
    # Placeholder for customer registration
    print(f"Registering customer: {customer_data['name']}")
    return {"customer_id": "123", "status": "registered"}

def setup_tenant(customer_id):
    # Setup tenant in multi-tenant system
    print(f"Setting up tenant for customer {customer_id}")
    return {"tenant_id": "tenant_123", "status": "setup"}

def configure_deployment(customer_id, config):
    # Configure deployment for customer
    print(f"Configuring deployment for {customer_id} with {config}")
    return {"deployment_id": "dep_123", "status": "configured"}

def onboard_customer(customer_data, config):
    customer = register_customer(customer_data)
    tenant = setup_tenant(customer['customer_id'])
    deployment = configure_deployment(customer['customer_id'], config)
    return {"onboarding_status": "complete", "details": {**customer, **tenant, **deployment}}