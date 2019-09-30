This is a little script to help make nicely-formatted photo albums. Use case:

* You want several photos on a page, nicely-aligned
* You want grouped by theme - could be date, but also "beach holidays", "dogs", "cathedrals"
* You don't mind losing a little control of the layout in return for this being relatively easy

This software is basically a command-line interface to the fabulous [PhotoCollage](https://github.com/adrienverge/PhotoCollage), with extra tag-grouping happiness.  You can see there the kind of output you can expect.

To do this:

* Use photo-editing software that allows you to tag your photos *and includes the tags in the metadata when you export them*. For example, I use Shotwell
* Tag them by theme - one tag per photo
* Export them to a folder
* Set up a virtualenv and run `pip install -r requirements.txt`
* Run something like `python3 collage.py --border-colour=white --width=1224 --height=1530 --random-page-seed=1 input_photos/*`
* Marvel at the outout in `out/`
* It's good to re-run several times with different `random-page-seed` numbers. This randomises the photo order. Then you can pick your favourite layout
* The max number of photos per page is currently hard-coded at 6 because that's what I needed. You should be able to change that pretty easily
