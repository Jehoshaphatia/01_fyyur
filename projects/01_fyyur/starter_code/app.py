#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from asyncio import futures
from distutils.log import error
import json
import sys
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from sqlalchemy import false, func, true
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import Venue, Show, Artist, app, db
import collections


# TODO: connect to a local postgresql database - TODO Completed see models.py

#----------------------------------------------------------------------------#
# Misc.
#----------------------------------------------------------------------------#
collections.Callable = collections.abc.Callable

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data - TODO Completed
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

    venue_locations_query = Venue.query.order_by(Venue.state, Venue.city).all()

    data = []

    for venue_location in venue_locations_query:
        venues_location_filter = Venue.query.filter_by(
            state=venue_location.state).filter_by(city=venue_location.city).all()
        venues = []
        for venue in venues_location_filter:
            venues.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': db.session.query(func.count(Show.venue_id)).filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()[0][0]
            })

        data.append({
            'city': venue_location.city,
            'state': venue_location.state,
            'venues': venues
        })

    return render_template('pages/venues.html', areas=data)


@ app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive. - TODO Completed
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_term = request.form.get('search_term', '')

    search_term_count_query = db.session.query(func.count(Venue.id)).filter(
        Venue.name.ilike(f'%{search_term}%')).all()

    search_result_filter = Venue.query.filter(
        Venue.name.ilike(f'%{search_term}%')).all()

    response = {
        "count": search_term_count_query[0][0],
        "data": search_result_filter
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id - TODO Completed

    venue_query = Venue.query.get(venue_id)

    venue_upcoming_shows_query = db.session.query(Show).join(Artist).filter(
        Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()

    venue_past_shows_query = db.session.query(Show).join(Artist).filter(
        Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()

    upcoming_shows = []

    for show in venue_upcoming_shows_query:
        new_upcoming_show = {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')

        }
        upcoming_shows.append(new_upcoming_show)

    past_shows = []

    for show in venue_past_shows_query:
        new_past_show = {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')

        }
        past_shows.append(new_past_show)

    data = {
        "id": venue_query.id,
        "name": venue_query.name,
        "genres": venue_query.genres,
        "address": venue_query.address,
        "city": venue_query.city,
        "state": venue_query.state,
        "phone": venue_query.phone,
        "website": venue_query.website,
        "facebook_link": venue_query.facebook_link,
        "seeking_talent": venue_query.seeking_talent,
        "seeking_description": venue_query.seeking_description,
        "image_link": venue_query.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@ app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@ app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead - TODO Completed
    # TODO: modify data to be the data object returned from db insertion - TODO Completed

    error = False
    try:
        new_venue = Venue()
        new_venue.name = request.form['name']
        new_venue.city = request.form['city']
        new_venue.state = request.form['state']
        new_venue.address = request.form['address']
        new_venue.phone = request.form['phone']
        new_venue.genres = request.form.getlist('genres')
        new_venue.facebook_link = request.form['facebook_link']
        new_venue.image_link = request.form['image_link']
        new_venue.website = request.form['website_link']
        new_venue.seeking_talent = True if 'seeking_talent' in request.form else False
        new_venue.seeking_description = request.form['seeking_description']

        db.session.add(new_venue)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

        # on successful db insert, flash success
        if not error:
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
        else:
            # TODO: on unsuccessful db insert, flash an error instead. - TODO Completed
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be listed.')

    return render_template('pages/home.html')


@ app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using - TODO Completed
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    error = False
    try:
        venue_query = Venue.query.get(venue_id)
        db.session.delete(venue_query)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if not error:
            flash('Venue ' + request.form['name'] +
                  ' was successfully deleted!')
        else:
            # TODO: on unsuccessful db insert, flash an error instead.- TODO Completed
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be deleted.')

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@ app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database - TODO Completed
    data = Artist.query.all()

    return render_template('pages/artists.html', artists=data)


@ app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive. - TODO Completed
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')

    search_term_count_query = db.session.query(func.count(Artist.id)).filter(
        Artist.name.ilike(f'%{search_term}%')).all()

    search_result_filter = Artist.query.filter(
        Artist.name.ilike(f'%{search_term}%')).all()

    response = {
        "count": search_term_count_query[0][0],
        "data": search_result_filter
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id - TODO Completed
    artist_query = Artist.query.get(artist_id)

    artist_upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id == artist_id).filter(
        Show.start_time > datetime.now()).all()

    artist_past_shows_query = db.session.query(Show).join(Artist).filter(
        Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()

    upcoming_shows = []

    for show in artist_upcoming_shows_query:
        new_upcoming_show = {
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')

        }
        upcoming_shows.append(new_upcoming_show)

    past_shows = []

    for show in artist_past_shows_query:
        new_past_show = {
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        past_shows.append(new_past_show)

    data = {
        "id": artist_query.id,
        "name": artist_query.name,
        "genres": artist_query.genres,
        "city": artist_query.city,
        "state": artist_query.state,
        "phone": artist_query.phone,
        "website": artist_query.website,
        "facebook_link": artist_query.facebook_link,
        "seeking_venue": artist_query.seeking_venue,
        "seeking_description": artist_query.seeking_description,
        "image_link": artist_query.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
 # TODO: populate form with fields from artist with ID <artist_id> - TODO Completed
    artist_query = Artist.query.get(artist_id)
    form.name.data = artist_query.name
    form.genres.data = artist_query.genres
    form.city.data = artist_query.city
    form.state.data = artist_query.state
    form.phone.data = artist_query.phone
    form.website_link.data = artist_query.website
    form.facebook_link.data = artist_query.facebook_link
    form.seeking_venue.data = artist_query.seeking_venue
    form.seeking_description.data = artist_query.seeking_description
    form.image_link.data = artist_query.image_link

    return render_template('forms/edit_artist.html', form=form, artist=artist_query)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing - TODO Completed
    # artist record with ID <artist_id> using the new attributes
    error = False
    artist_query = Artist.query.get(artist_id)
    try:
        artist_query.name = request.form['name']
        artist_query.genres = request.form.getlist('genres')
        artist_query.city = request.form['city']
        artist_query.state = request.form['state']
        artist_query.phone = request.form['phone']
        artist_query.website = request.form['website_link']
        artist_query.facebook_link = request.form['facebook_link']
        artist_query.seeking_venue = True if 'seeking_venue' in request.form else False
        artist_query.seeking_description = request.form['seeking_description']
        artist_query.image_link = request.form['image_link']
        db.session.add(artist_query)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if not error:
            flash('Artist ' + request.form['name'] +
                  ' was successfully updated!')
        else:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be updated.')

    return redirect(url_for('show_artist', artist_id=artist_id))


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    # TODO: populate form with values from venue with ID <venue_id> - TODO Completed
    venue__query = Venue.query.get(venue_id)
    form.name.data = venue__query.name
    form.genres.data = venue__query.genres
    form.address.data = venue__query.address
    form.city.data = venue__query.city
    form.state.data = venue__query.state
    form.phone.data = venue__query.phone
    form.website_link.data = venue__query.website
    form.facebook_link.data = venue__query.facebook_link
    form.seeking_talent.data = venue__query.seeking_talent
    form.seeking_description.data = venue__query.seeking_description
    form.image_link.data = venue__query.image_link

    return render_template('forms/edit_venue.html', form=form, venue=venue__query)


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing - TODO Completed
    # venue record with ID <venue_id> using the new attributes
    error = False
    venue__query = Venue.query.get(venue_id)
    try:
        venue__query.name = request.form['name']
        venue__query.genres = request.form.getlist('genres')
        venue__query.address = request.form['address']
        venue__query.city = request.form['city']
        venue__query.state = request.form['state']
        venue__query.phone = request.form['phone']
        venue__query.website = request.form['website_link']
        venue__query.facebook_link = request.form['facebook_link']
        venue__query.seeking_talent = True if 'seeking_talent' in request.form else False
        venue__query.seeking_description = request.form['seeking_description']
        venue__query.image_link = request.form['image_link']
        db.session.add(venue__query)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if not error:
            flash('Venue ' + request.form['name'] +
                  ' was successfully updated!')
        else:
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be updated.')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@ app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@ app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead - TODO Completed
    # TODO: modify data to be the data object returned from db insertion - TODO Completed

    error = False
    try:
        new_artist = Artist()
        new_artist.name = request.form['name']
        new_artist.city = request.form['city']
        new_artist.state = request.form['state']
        new_artist.phone = request.form['phone']
        new_artist.genres = request.form.getlist('genres')
        new_artist.facebook_link = request.form['facebook_link']
        new_artist.image_link = request.form['image_link']
        new_artist.website = request.form['website_link']
        new_artist.seeking_venue = True if 'seeking_venue' in request.form else False
        new_artist.seeking_description = request.form['seeking_description']

        db.session.add(new_artist)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

        # on successful db insert, flash success
        if not error:
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
        else:
            # TODO: on unsuccessful db insert, flash an error instead. - TODO Completed
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@ app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data. - TODO Completed

    all_shows_query = db.session.query(Show).join(Artist).join(Venue).all()

    data = []

    for show in all_shows_query:
        new_show = {
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        data.append(new_show)

    return render_template('pages/shows.html', shows=data)


@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead - TODO Completed

    error = False
    try:
        new_show = Show()
        new_show.artist_id = request.form['artist_id']
        new_show.venue_id = request.form['venue_id']
        new_show.start_time = request.form['start_time']

        db.session.add(new_show)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

        # on successful db insert, flash success
        if not error:
            flash('Show was successfully listed!')
        else:
            # TODO: on unsuccessful db insert, flash an error instead. - TODO Completed
            flash('An error occurred. Show could not be listed.')

    return render_template('pages/home.html')


@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(host="localhost", port=8080)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
