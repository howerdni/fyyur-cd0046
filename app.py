#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from forms import *
from flask_migrate import Migrate

from datetime import datetime
import re
from model import Genre, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# connect to a local postgresql database
migrate = Migrate(app, db)



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


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
   
    venues=db.session.query(Venue).join(Venue.shows).order_by('state','city', 'id').all()
    data = [] 
    now = datetime.now()
    for i in venues:
        venue_info = []
        #venue_shows = Show.query.filter_by(venue_id=i.id).all()
        num_upcoming = 0       
        for show in i.shows:
            if show.start_time > now:
                num_upcoming += 1 
        venue_info.append({
            "id": i.id,
            "name": i.name,
            "num_upcoming_shows": num_upcoming
        })
        data.append({
            "city": i.city,
            "state": i.state,
            "venues": venue_info
        })
        
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '').strip()

    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    venue_list = []
    now = datetime.now()
    for venue in venues:
    
        venue_list.append({
            "id": venue.id,
            "name": venue.name,

        })

    response = {
        "count": len(venues),
        "data": venue_list
    }

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    data = Venue.query.filter_by(id=venue_id).first()
    #genres = [genre.name for genre in data.genres]
    
    past_shows = []
    past_shows_count = 0
    upcoming_shows = []
    upcoming_shows_count = 0
    
    now = datetime.now()
    for show in data.shows:
      if show.start_time > now:
        upcoming_shows_count += 1
        upcoming_shows.append(show)
      else:
        past_shows_count += 1
        past_shows.append(show)
    data.upcoming_shows = upcoming_shows
    data.past_shows = past_shows
    data.upcoming_shows_count=upcoming_shows_count
    data.past_shows_count=upcoming_shows_count
    #data.genres=genres
    data.phone=(data.phone[:3] + '-' + data.phone[3:6] + '-' + data.phone[6:])

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()

    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    address = form.address.data.strip()
    phone = form.phone.data
    # relace any char not a numnber with '' in the string phone
    phone = re.sub('\D', '', phone)
    genres = form.genres.data # it's a list of strings
    seeking_talent = True if form.seeking_talent.data == 'Yes' else False
    seeking_description = form.seeking_description.data.strip()
    image_link = form.image_link.data.strip()
    website = form.website.data.strip()
    facebook_link = form.facebook_link.data.strip()
    
    error_in_insert=False
    try:
        added_venue = Venue(name=name, city=city, state=state, address=address, phone=phone, \
            seeking_talent=seeking_talent, seeking_description=seeking_description, image_link=image_link, \
            website=website, facebook_link=facebook_link)
        for genre in genres:
            genre_obj = Genre.query.filter_by(name=genre).one_or_none() 
            if genre_obj:
                # add_venue.genres is a list of genre objects
                added_venue.genres.append(genre_obj)
        db.session.add(new_venue)
        db.session.commit()
    except Exception as e:
        error_in_insert = True
        print(f'Exception "{e}" in create_venue_submission()')
        db.session.rollback()
    finally:
        db.session.close()
    if not error_in_insert:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully posted!')
        return redirect(url_for('index'))
    else:
        flash('An error occurred during posting Venue ' + name )
        print("Error in create_venue_submission()")
        abort(500)


@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
    
    venue = Venue.query.get(venue_id)
    if not venue:
        
        return redirect(url_for('index'))
    else:
        error_on_delete = False
        try:
            db.session.delete(venue)
            db.session.commit()
        except:
            error_on_delete = True
            db.session.rollback()
        finally:
            db.session.close()
        if error_on_delete:
            flash(f'An error occurred during deleting venue {venue.name}.')
            print("Error in delete_venue()")
            abort(500)
        else:
            return jsonify({
                'deleted': True,
                'url': url_for('venues')
            })


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.order_by(Artist.id).all()  # Sort alphabetically

    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })


    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # Most code is the same with venue_search
    search_term = request.form.get('search_term', '').strip()

    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all() 
    artist_list = []
    now = datetime.now()
    for artist in artists:
        artist_shows = Show.query.filter_by(artist_id=artist.id).all()
        num_upcoming = 0
        for show in artist_shows:
            if show.start_time > now:
                num_upcoming += 1

        artist_list.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming  
        })

    response = {
        "count": len(artists),
        "data": artist_list
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    data = Artist.query.filter_by(id=artist_id).first()
    if not data:
        return redirect(url_for('index'))
    else:

        past_shows = []
        past_shows_count = 0
        upcoming_shows = []
        upcoming_shows_count = 0
        now = datetime.now()
        for show in data.shows:
            if show.start_time > now:
                upcoming_shows_count += 1
                upcoming_shows.append(show)
            if show.start_time < now:
                past_shows_count += 1
                past_shows.append(show)
        data.upcoming_shows = upcoming_shows
        data.past_shows = past_shows
        data.upcoming_shows_count=upcoming_shows_count
        data.past_shows_count=upcoming_shows_count
        data.phone=(data.phone[:3] + '-' + data.phone[3:6] + '-' + data.phone[6:])


    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

    artist = Artist.query.get(artist_id) 
    if not artist:
        return redirect(url_for('index'))
    else:

        form = ArtistForm(obj=artist)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
#get the data from the form
    form = ArtistForm()
    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    phone = form.phone.data
    phone = re.sub('\D', '', phone)
    genres = form.genres.data
    seeking_venue = True if form.seeking_venue.data == 'Yes' else False
    seeking_description = form.seeking_description.data.strip()
    image_link = form.image_link.data.strip()
    website = form.website.data.strip()
    facebook_link = form.facebook_link.data.strip()
    error_in_update = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = name
        artist.city = city
        artist.state = state
        artist.phone = phone
        artist.seeking_venue = seeking_venue
        artist.seeking_description = seeking_description
        artist.image_link = image_link
        artist.website = website
        artist.facebook_link = facebook_link
        artist.genres = []
        
        for genre in genres:
            genre_obj = Genre.query.filter_by(name=genre).one_or_none()  
            artist.genres.append(genre_obj)

        db.session.commit()
    except Exception as e:
        error_in_update = True
        print(f'Exception "{e}" occurred in editing artist after submission')
        db.session.rollback()
    finally:
        db.session.close()
    if not error_in_update:
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
        return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        flash('An error occurred. Artist ' + name + ' could not be updated.')
        abort(500)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

    venue = Venue.query.get(venue_id) 
    if not venue:
        return redirect(url_for('index'))
    else:

        form = VenueForm(obj=venue)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

    form = VenueForm()

    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    address = form.address.data.strip()
    phone = form.phone.data
    phone = re.sub('\D', '', phone)
    genres = form.genres.data                   
    seeking_talent = True if form.seeking_talent.data == 'Yes' else False
    seeking_description = form.seeking_description.data.strip()
    image_link = form.image_link.data.strip()
    website = form.website.data.strip()
    facebook_link = form.facebook_link.data.strip()
    error_in_update = False
    try:
        venue = Venue.query.get(venue_id)
        #Update the venue
        venue.name = name
        venue.city = city
        venue.state = state
        venue.address = address
        venue.phone = phone
        venue.seeking_talent = seeking_talent
        venue.seeking_description = seeking_description
        venue.image_link = image_link
        venue.website = website
        venue.facebook_link = facebook_link

        venue.genres = []
        for genre in genres:
            genre_obj = Genre.query.filter_by(name=genre).one_or_none()                  
            venue.genres.append(genre_obj)
        db.session.commit()
    except Exception as e:
        error_in_update = True
        print(f'Exception "{e}"  in calling edit_venue_submission()')
        db.session.rollback()
    finally:
        db.session.close()
    if not error_in_update:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
        return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        flash('An error occurred. Venue ' + name + ' could not be updated.')
        abort(500)


#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():


    form = ArtistForm()

    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    phone = form.phone.data
    phone = re.sub('\D', '', phone) 
    genres = form.genres.data                   
    seeking_venue = True if form.seeking_venue.data == 'Yes' else False
    seeking_description = form.seeking_description.data.strip()
    image_link = form.image_link.data.strip()
    website = form.website.data.strip()
    facebook_link = form.facebook_link.data.strip()
    error_in_insert=False
    try:

        added_artist = Artist(name=name, city=city, state=state, phone=phone, seeking_venue=seeking_venue, \
            seeking_description=seeking_description, image_link=image_link, \
            website=website, facebook_link=facebook_link)
        for genre in genres:
            genre_obj = Genre.query.filter_by(name=genre).one_or_none()  
            added_artist.genres.append(genre_obj)

        db.session.add(added_artist)
        db.session.commit()
    except Exception as e:
        error_in_insert = True
        print(f'Exception "{e}" when calling create_artist_submission()')
        db.session.rollback()
    finally:
        db.session.close()
    if not error_in_insert:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return redirect(url_for('index'))
    else:
        flash('An error occurred. Artist ' + name + ' could not be listed.')
        abort(500)

@app.route('/artists/<artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):
    artist = Artist.query.get(artist_id)
    if not artist:
        return redirect(url_for('index'))
    else:
        error_on_delete = False
        artist_name = artist.name
        try:
            db.session.delete(artist)
            db.session.commit()
        except:
            error_on_delete = True
            db.session.rollback()
        finally:
            db.session.close()
        if error_on_delete:
            flash(f'An error occurred deleting artist {artist_name}.')
            print("Error in delete_artist()")
            abort(500)
        else:
            return jsonify({
                'deleted': True,
                'url': url_for('artists')
            })


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows

    shows = Show.query.all()
    data=shows

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create', methods=['GET'])
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()

    artist_id = form.artist_id.data.strip()
    venue_id = form.venue_id.data.strip()
    start_time = form.start_time.data
    error_in_insert=False
    try:
        new_show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)
        db.session.add(new_show)
        db.session.commit()
    except:
        error_in_insert = True
        print(f'Exception "{e}" when calling create_show_submission()')
        db.session.rollback()
    finally:
        db.session.close()

    if error_in_insert:
        flash(f'An error occurred. Show could not be created.')
        print("Error in calling create_show_submission()")
    else:
        flash('Show was successfully created!')
    
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
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
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
