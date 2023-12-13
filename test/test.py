event = Event.query.get(event_id)
event.title = 'Updated Title'
db.session.commit()

