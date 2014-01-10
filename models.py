import os
from StringIO import StringIO

from sqlalchemy import Table, Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from PIL import Image
from lxml import etree
import requests

from settings import *

Base = declarative_base()
engine = create_engine('mysql://{0}:{1}@{2}:{3}/{4}'.format( 
                       DATABASE['user'], 
                       DATABASE['password'], 
                       DATABASE['host'], 
                       DATABASE['port'], 
                       DATABASE['name']))
Session = sessionmaker(bind=engine)

class ImageModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    _path = Column(String(1024))
    height = Column(Integer)
    width = Column(Integer)

    @property
    def path(self):
        return str(APP_ROOT) + self._path
    
    def __repr__(self):
        return '<{0}: {1}>'.format(self.__class__.__name__, self.__unicode__())

    def __unicode__(self):
        return ''

class FlickrImage(ImageModel):
    __tablename__ = 'flickr_images'
    flickr_user = Column(String(255))
    flickr_src = Column(String(1024))

    def get_cropped(self, width, height, session):
        r = session.query(CroppedFlickrImage).filter(
            CroppedFlickrImage.full_img==self, 
            CroppedFlickrImage.height==height, 
            CroppedFlickrImage.width==width).all()
        if r:
            return r[0]

        else:
            # Crop image
            i = Image.open(self.path)
            d_ratio = float(width) / float(height)
            i_ratio = float(self.width) / float(self.height)
            corners = (0, 0, 0, 0) # (left, top, right, bottom)
            # If image is shorter than desired image, make height full height
            if i_ratio > d_ratio:
                w = int(round(self.height * d_ratio))
                padding = int(round((self.width - w) / 2))
                corners = (padding, 0, padding + w, self.height)
            # If image is thinner than desired image, make width full width
            else:
                h = int(round(self.width / d_ratio))
                padding = int(round((self.height - h) / 2))
                corners = (0, padding, self.width, padding + h)
            i = i.crop(corners)
            # Resize image
            i = i.resize((width, height), Image.ANTIALIAS)
            
            # Make CropppedFlickrImage
            rsrc_folder = '/'.join(self.path.split('/')[:-2])
            filename = self.path.split('/')[-1]
            name = '.'.join(filename.split('.')[:-1])
            ext = filename.split('.')[-1]
            new_filename = '{0}_{1}X{2}.{3}'.format(name, width, height, ext)
            new_img = CroppedFlickrImage(
                _path=rsrc_folder + '/thumbnails/' + new_filename,
                width=width,
                height=height,
                image_id=self.id
            )
            i.save(new_img.path)
            session.add(new_img)
            session.commit()
            return new_img

    def __unicode__(self):
        return self.path


class CroppedFlickrImage(ImageModel):
    __tablename__ = 'cropped_flickr_images'
    image_id = Column(Integer, ForeignKey('flickr_images.id'))
    full_img = relationship('FlickrImage', backref='cropped')

    def show(self):
        Image.open(self.path).show()

    def __unicode__(self):
        return self.path


def seed_db(session):
    with open('data/flickr_links.txt') as f:
        for url in f.readlines():
            url = url.strip()

            r = session.query(FlickrImage).filter(FlickrImage.flickr_src==url)
            if (list(r)):
                print str(r[0]) + ' already in database'
                continue

            html = requests.get(url).text
            tree = etree.parse(StringIO(html), etree.HTMLParser())
            user_elt = tree.xpath('//span[@class="photo-name-line-1"]/a')[0]
            user = user_elt.text.strip()

            full_url = url + 'sizes/o/in/photostream/'
            full_html = requests.get(full_url).text
            full_tree = etree.parse(StringIO(full_html), etree.HTMLParser())
            img_elt = full_tree.xpath('//div[@id="allsizes-photo"]/img')[0]
            img_src = img_elt.get('src').strip()
            filename = img_src.split('/')[-1]

            img_content = requests.get(img_src).content
            img = Image.open(StringIO(img_content))

            with open('resources/full_res/' + filename, 'w') as img_file:
                img_file.write(img_content)

            db_img = FlickrImage(
                _path='resources/full_res/' + filename,
                height=img.size[1],
                width=img.size[0],
                flickr_user=user,
                flickr_src=url
            ) 
            print db_img
            session.add(db_img)
    session.commit()

if __name__ == '__main__':
    s = Session()
    seed_db(s)
    s.close()
