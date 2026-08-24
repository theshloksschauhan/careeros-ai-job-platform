import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from datetime import datetime, timezone

from server import current_user, db, serialize_app

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")
PRICE_ID_10_CREDITS = os.environ.get("STRIPE_PRICE_ID_10_CREDITS", "price_placeholder")

stripe_router = APIRouter(prefix="/api/stripe")

@stripe_router.post("/checkout")
async def create_checkout_session(user: dict = Depends(current_user)):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': PRICE_ID_10_CREDITS,
                'quantity': 1,
            }],
            mode='payment',
            success_url=os.environ.get("FRONTEND_URL", "http://localhost:3000") + "/billing?success=true",
            cancel_url=os.environ.get("FRONTEND_URL", "http://localhost:3000") + "/billing?canceled=true",
            client_reference_id=user["id"],
            metadata={
                "user_id": user["id"],
                "credits": 10
            }
        )
        return {"id": session.id, "url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stripe_router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return Response(status_code=400)
    except stripe.error.SignatureVerificationError as e:
        return Response(status_code=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        credits_to_add = int(session.get('metadata', {}).get('credits', 10))
        customer_id = session.get('customer')

        if user_id:
            from bson import ObjectId
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$inc": {"credits": credits_to_add},
                    "$set": {"stripe_customer_id": customer_id}
                }
            )

    return {"status": "success"}

@stripe_router.get("/credits")
async def get_credits(user: dict = Depends(current_user)):
    from bson import ObjectId
    user_doc = await db.users.find_one({"_id": ObjectId(user["id"])})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Give free 3 credits if not set
    credits = user_doc.get("credits")
    if credits is None:
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": {"credits": 3}})
        credits = 3
        
    return {"credits": credits}
