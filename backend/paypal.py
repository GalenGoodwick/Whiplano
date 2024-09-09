import braintree

gateway = braintree.BraintreeGateway(
  braintree.Configuration(
      braintree.Environment.Sandbox,
      merchant_id="use_your_merchant_id",
      public_key="use_your_public_key",
      private_key="use_your_private_key"
  )
)