import mimetypes
from random import randrange

from flask import Flask, abort, send_file

from models import FlickrImage, CroppedFlickrImage, Session
s = Session()

app = Flask(__name__)
app.config.from_object('settings')

@app.route('/<int:width>/<int:height>/')
def get_image(width, height):
    s = Session()
    ratio = float(width) / height
    imgs = []
    for img in s.query(FlickrImage).all():
        imgs.append({
            'ratio_diff': abs((float(img.width) / img.height) - ratio),
            'img': img
        })
    imgs = sorted(imgs, key=lambda d: d['ratio_diff'])
    # Choose a random image to spice things up a bit ;)
    img = imgs[randrange(4)]['img']
    cropped = img.get_cropped(width, height, s)
    sf = send_file(cropped.path, mimetypes.guess_type(cropped.path)[0])
    s.close()
    return sf

@app.route('/<int:img_id>/<int:width>/<int:height>/')
def get_by_id(img_id, width, height):
    s = Session()
    img = s.query(FlickrImage).filter(FlickrImage.id==img_id).first()
    if not img:
        abort(404)
    cropped = img.get_cropped(width, height, s)
    sf = send_file(cropped.path, mimetypes.guess_type(cropped.path)[0])
    s.close()
    return sf


if __name__ == '__main__':
    app.debug = True
    app.run()
