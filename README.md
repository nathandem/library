# Introduction 
Small personal project created to practice python and django.
I'm open to any technical suggestion and remark :)


# Forwards

## Blocking
- complete test coverage of the existing perimeter
- add select_related() to all subscriber and librarian queries

## Short-term:
- create the booking views, the associated mgt commands and reflect the changes introduced by this feature to the rest of the code
- create a search feature, at close as possible from the stock django querysets
- make a frontend: django admin for the resource modification is enough, JS front for the rest

## Mid-term:
- set-up a email back-end
- deploy the app
- add more data (pay close attention to the migrations not to lose a single drop of data)
- test the app in a real situation (need to find people interested)
- don't rely on email as username for subscribers, they can change their emails and we then don't want to stick with their old emails as usernames

## Later:
- store images for the books and subscribers
- add analytics
