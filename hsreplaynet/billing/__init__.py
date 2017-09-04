from djstripe import webhooks


@webhooks.handler("customer.subscription.created")
def sync_premium_accounts_for_subscription(event):
	from hsreplaynet.analytics.processing import (
		enable_premium_accounts_for_users_in_redshift
	)
	if event.customer and event.customer.subscriber:
		user = event.customer.subscriber
		enable_premium_accounts_for_users_in_redshift([user])
