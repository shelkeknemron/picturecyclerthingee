#!/usr/bin/python3

from argparse import ArgumentParser
from os import listdir
from os.path import abspath, basename, dirname, expanduser, isdir, isfile
from re import search
from subprocess import getoutput
from xml.dom.minidom import Document


# Class: GnomeXMLWallpaper
# Class for generating a Gnome XML slideshow file from a directory of images.
class GnomeXMLWallpaper(object):
    # Constructor: __init__
    # Initializes core settings.
    #
    # Parameters:
    #     directory - The directory containing images to use in the image slideshow.
    #     duration - The amount of time an image should remain in view.
    #     transition - The amount of time to transition between images.
    #
    # Class Properties:
    #     self.directory - The absolute path to the target images directory.
    #     self.filename - The filename for the XML slideshow.
    #     self.duration - Duration time converted to seconds.
    #     self.transition - Transition time converted to seconds.
    #     self.allowed_types - Not really sure which image types are supported for Gnome slideshow, but JPG and PNG are definitely safe.
    def __init__(self, directory, duration, transition):
        path = expanduser(directory).rstrip("/")
        if isdir(path):
            self.directory = abspath(path)
        else:
            self.directory = None
        self.filename = basename(self.directory)
        self.duration = self._to_seconds(duration)
        self.transition = self._to_seconds(transition)
        self.allowed_types = ["image/jpeg", "image/png"]

    # Method: _to_seconds
    # Static method for converting text into seconds.
    #
    # Parameters:
    #     time_string - A string representing a period of time in days, hours, minutes, or seconds. If no time delineation is provided, seconds are assumed.
    #
    # Returns:
    #     amount * multiplier - The number of seconds in the interval described by time_string.
    @staticmethod
    def _to_seconds(time_string):
        pattern = r"^([1-9][0-9]*)(\s?([dDhHmMsS])[\w]*)?"
        match = search(pattern, time_string)
        if match:
            if isinstance(match.group(1), str):
                amount = int(match.group(1))
            else:
                return None

            delineation = None
            if match.group(3):
                delineation = match.group(3).lower()

            if delineation == "d":
                multiplier = 86400
            elif delineation == "h":
                multiplier = 3600
            elif delineation == "m":
                multiplier = 60
            else:
                multiplier = 1

        return amount * multiplier

    # Method: find_images
    # Method for listing files and finding allowed image types. The use of subprocess.getoutput to call the file command makes it so that this method will only
    # work in *nix operating systems that have the file command available.

    # Returns:
    #     A list of full paths to images within self.directory.
    def find_images(self):
        file_list = listdir(self.directory)

        images = []
        for filename in file_list:
            fullpath = "{}/{}".format(self.directory, filename)
            if isfile(fullpath):
                file_type = getoutput("file --mime-type {}".format(fullpath)).split()[-1]
                if file_type in self.allowed_types:
                    images.append(fullpath)

        return images

    # Method: make_xml
    # Method for writing an XML slideshow file compatible with Gnome.
    #
    # Parameters:
    #     images - A list of full image paths to include in the slideshow.
    #
    # Output:
    #     xml_file - The Gnome XML slideshow.
    #
    # See Also:
    #     <find_images>
    def make_xml(self, images):
        doc = Document()
        background = doc.createElement("background")
        doc.appendChild(background)

        element = 0
        while element < len(images):
            static = doc.createElement("static")
            background.appendChild(static)
            duration = doc.createElement("duration")
            static.appendChild(duration)
            text = doc.createTextNode("{}.0".format(str(self.duration)))
            duration.appendChild(text)
            file = doc.createElement("file")
            static.appendChild(file)
            text = doc.createTextNode(images[element])
            file.appendChild(text)

            transition = doc.createElement("transition")
            background.appendChild(transition)
            duration = doc.createElement("duration")
            transition.appendChild(duration)
            text = doc.createTextNode("{}.0".format(str(self.transition)))
            duration.appendChild(text)
            from_elem = doc.createElement("from")
            transition.appendChild(from_elem)
            text = doc.createTextNode(images[element])
            from_elem.appendChild(text)

            if element + 1 == len(images):
                next_element = 0
            else:
                next_element = element + 1

            to = doc.createElement("to")
            transition.appendChild(to)
            text = doc.createTextNode(images[next_element])
            to.appendChild(text)

            element += 1

        pretty_print = doc.toprettyxml(indent='    ')
        with open("{}/{}.xml".format(self.directory, self.filename), "w") as xml_file:
            xml_file.write(pretty_print)


# Class: GnomeXMLInputParser
# Class that provides a terminal user interface for generating an XML slideshow.
#
# See Also:
#     <GnomeXMLWallpaper>
class GnomeXMLInputParser(object):
    # Constructor: __init__
    # ArgumentParser construction and interface argument definitions.
    #
    # Arguments:
    #     -p, --path - The directory path from which to add images to the wallpaper. Only jpeg and png files are supported (default=~/Pictures).
    #     -d, --duration - The period of time a wallpaper should be displayed (default=1h). Can be specified in d[ays], h[ours], m[inutes], or s[econds]
    #                      (e.g. 15m).
    #     -t, --transition - The period of time (in s[econds]) that one image should cross-fade to another (default=2s).
    #
    # Calls <generate_xml> to process user input.
    def __init__(self):
        help_text = {
            "description": "Generates a slideshow wallpaper file for Gnome.",
            "path": "The directory path from which to add images to the wallpaper. Only jpeg and png files are supported (default=~/Pictures).",
            "duration": "The period of time a wallpaper should be displayed (default=1h). Can be specified in d[ays], h[ours], m[inutes], or s[econds] \
                        (e.g. 15m).",
            "transition": "The period of time (in s[econds]) that one image should cross-fade to another (default=2s)."
        }

        parser = ArgumentParser(description=help_text["description"])
        parser.add_argument("-p", "--path", metavar="directory", nargs=1, help=help_text["path"], default=["~/Pictures"])
        parser.add_argument("-d", "--duration", metavar="time", nargs=1, help=help_text["duration"], default=["3600"])
        parser.add_argument("-t", "--transition", metavar="time", nargs=1, help=help_text["transition"], default=["2"])
        parser.set_defaults(func=self.generate_xml)

        args = parser.parse_args()
        args.func(args)

    # Method: generate_xml
    # Method for validating user input and calling <GnomeXMLWallpaper> with required parameters.
    #
    # Returns:
    #     True - When all user input is valid and an XML file has been produced.
    #     False - When there is invalid user input, or the target directory does not contain accepted image formats.
    #
    # See Also:
    #     <__init__>
    @staticmethod
    def generate_xml(args):
        wallpaper = GnomeXMLWallpaper(args.path[0], args.duration[0], args.transition[0])
        if isinstance(wallpaper.duration, int):
            print("Slide duration time: {} seconds".format(str(wallpaper.duration)))
        else:
            print("Duration time is invalid.")
            return False

        if isinstance(wallpaper.transition, int):
            print("Slide transition time: {} seconds".format(str(wallpaper.transition)))
        else:
            print("Transition time is invalid.")
            return False

        if isinstance(wallpaper.directory, str):
            print("Slide image directory: {}".format(wallpaper.directory))
        else:
            print("Path is not a valid directory.")
            return False

        images = wallpaper.find_images()
        if not images:
            print("No images were found in the directory path.")
            return False

        print("The following images have been added to the slideshow:\n{}".format("\n".join(images)))
        wallpaper.make_xml(images)
        return True


# If this script is actually run and NOT imported, call <GnomeXMLInputParser>.
if __name__ == '__main__':
    main = GnomeXMLInputParser()
