Small personal project to practice crafting a webapp with python and django.
I'm open to any technical suggestion and remark :)


# Forwards

## Short-term:
- create a search feature, at close as possible from the stock django querysets
- make a frontend: django admin for the resource modification is enough, JS front for the rest

## Mid-term:
- set-up an email templating and an email back-end
- deploy the app
- add more data (pay close attention to the migrations not to lose a single drop of data)
- test the app in a real situation (need to find people interested)
- don't rely on email as username for subscribers, they can change their emails and we then don't want to stick with their old emails as usernames

## Later:
- store images for the books and subscribers
- add analytics
- include un endpoint schema
- include payment API (for the fun of testing it)

## Maybe
- create a subscription table to have different types of subscription, and potentially subscription for several subscribers (like a family plan)
- attach a QR code to subscribers, apparently some python library do that
