"""Script that uses the excellent PhotoCollage package to process
input files and group them by IPTC keyword into pages.

"""
import argparse
import math
import os
import random
import sys
from iptcinfo3 import IPTCInfo

# from PIL import Image

from photocollage import collage
from photocollage import render


class UserCollage(object):
    """Represents a user-defined collage
    A UserCollage contains a list of photos (referenced by filenames) and a
    collage.Page object describing their layout in a final poster.
    """

    def __init__(self, photolist):
        self.photolist = photolist

    def make_page(self, opts):
        # Define the output image height / width ratio
        ratio = 1.0 * opts.out_h / opts.out_w

        # Compute a good number of columns. It depends on the ratio, the number
        # of images and the average ratio of these images. According to my
        # calculations, the number of column should be inversely proportional
        # to the square root of the output image ratio, and proportional to the
        # square root of the average input images ratio.
        avg_ratio = sum(1.0 * photo.h / photo.w for photo in self.photolist) / len(
            self.photolist
        )
        # Virtual number of images: since ~ 1 image over 3 is in a multi-cell
        # (i.e. takes two columns), it takes the space of 4 images.
        # So it's equivalent to 1/3 * 4 + 2/3 = 2 times the number of images.
        virtual_no_imgs = 2 * len(self.photolist)
        no_cols = int(round(math.sqrt(avg_ratio / ratio * virtual_no_imgs)))

        self.page = collage.Page(1.0, ratio, no_cols)
        random.shuffle(self.photolist)
        for photo in self.photolist:
            self.page.add_cell(photo)
        self.page.adjust()

    def duplicate(self):
        return UserCollage(copy.copy(self.photolist))


class Options(object):
    """An options object as expected by PhotoCollage
    """

    def __init__(self, args):
        self.border_w = args.border_width / 100
        self.border_c = args.border_colour
        self.out_w = args.width
        self.out_h = args.height


def save_poster(savefile, opts, collage):
    enlargement = float(opts.out_w) / collage.page.w
    collage.page.scale(enlargement)
    t = render.RenderingTask(
        collage.page,
        output_file=savefile,
        border_width=opts.border_w * max(collage.page.w, collage.page.h),
        border_color=opts.border_c,
    )
    t.start()


def make_poster(filename, new_images, args):
    photolist = []
    photolist.extend(render.build_photolist(new_images))
    opts = Options(args)
    if len(photolist) > 0:
        new_collage = UserCollage(photolist)
        new_collage.make_page(opts)
        save_poster(filename, opts, new_collage)


def make_big_groups(photo_filenames):
    """Group images by keyword
    """
    grouped = {}
    for photo_filename in photo_filenames:
        info = IPTCInfo(photo_filename)
        for x in info["keywords"]:
            x = x.decode("utf-8")
            if x not in grouped:
                grouped[x] = []
            grouped[x].append(photo_filename)
    return grouped


def split_into_balanced_groups_of(max_size, tag, items):
    """Given an array of `items`, split into equally-balanced groups, each no bigger than `max_size`
    """
    balanced_groups = {}
    # if you can divide it equally by num_groups, return
    num_items = len(items)

    # Find the smallest number of groups we can split into
    num_groups = 1
    while True:
        if num_items / num_groups <= max_size:
            break
        num_groups += 1
        assert num_groups < 20, "Too many subgroups!"

    spare_items = num_items % num_groups
    # create equal size groups
    group_sizes = [int((num_items - spare_items) / num_groups)] * num_items
    # distribute the remainder equitably amongst those groups
    for i in range(0, spare_items + 1):
        group_sizes[i] += 1
    group_start_index = 0
    for group_number, group_size in enumerate(group_sizes):
        group_end_index = group_start_index + group_size
        balanced_groups["{}_{}".format(tag, group_number)] = items[
            group_start_index:group_end_index
        ]
        group_start_index = group_end_index
    return balanced_groups


def split_groups(groups):
    """Take images grouped by keyword, and subdivide the groups into
    subgroups of no more than max_size.

    """
    splitted_groups = {}
    max_size = 6
    for tag, images in groups.items():
        splitted_groups.update(split_into_balanced_groups_of(max_size, tag, images))
    return splitted_groups


def grouped(photo_filenames):
    return split_groups(make_big_groups(photo_filenames))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--border-colour",
        default="black",
        help="Border colour as rgb hex (prefixed with #) or X11 color name",
    )
    parser.add_argument(
        "--border-width",
        type=int,
        default=1,
        help="Border width as a percentage of the largest dimension",
    )
    parser.add_argument("--width", type=int, default=800, help="width in pixels")
    parser.add_argument("--height", type=int, default=600, help="height in pixels")
    parser.add_argument(
        "--random-album-seed",
        type=int,
        default=1,
        help="random seed for overall photo ordering",
    )
    parser.add_argument(
        "--random-page-seed",
        type=int,
        default=2,
        help="random seed for ordering within a page",
    )
    parser.add_argument(
        "photo_filenames", nargs="+", help="List of paths to photo files"
    )
    args = parser.parse_args()
    os.makedirs("out", exist_ok=True)
    import logging

    iptcinfo_logger = logging.getLogger("iptcinfo")
    iptcinfo_logger.setLevel(logging.ERROR)
    random.seed(args.random_album_seed)
    random.shuffle(args.photo_filenames)
    random.seed(args.random_page_seed)
    for tag, photos in grouped(args.photo_filenames).items():
        make_poster("out/{}.jpg".format(tag), photos, args)
