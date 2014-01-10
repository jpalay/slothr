import mimetypes

from flask import Flask, send_file

from models import FlickrImage, CroppedFlickrImage, Session
s = Session()

app = Flask(__name__)
app.config.from_object('settings')

@app.route('/<int:width>/<int:height>/')
def get_image(width, height):
    ratio = float(width) / height
    s = Session()
    imgs = []
    for img in s.query(FlickrImage).all():
        imgs.append({
            'ratio_diff': abs((float(img.width) / img.height) - ratio),
            'img': img
        })
    imgs = sorted(imgs, key=lambda d: d['ratio_diff'])
    img = imgs[0]['img']
    cropped_img = img.get_cropped(width, height, s)
    sf = send_file(cropped_img.path, mimetypes.guess_type(cropped_img.path)[0])
    s.close()
    return sf

if __name__ == '__main__':
    app.debug = True
    app.run()
