#!/usr/bin/env python
#
# NAME
#
#        med2image
#
# DESCRIPTION
#
#        'med2image' converts from medical image data files to
#        display-friendly formats (like png and jpg).
#
# HISTORY
#
# 23 February 2015
# o Initial design and coding.
#

# System imports
import     os
import     sys
import     getpass
import     argparse
import     time
import     numpy             as         np
from       random            import     randint

# System dependency imports
import     nibabel           as         nib
import     dicom
import     pylab
import     matplotlib.cm     as         cm

# Project specific imports
from       _common           import     systemMisc     as misc
from       _common._colors   import     Colors
from       _common           import     error
from       _common           import     message        as msg

class med2image(object):
    """
        med2image accepts as input certain medical image formatted data
        and converts each (or specified) slice of this data to a graphical
        display format such as png or jpg.

    """

    _dictErr = {
        'inputFileFail'   : {
            'action'        : 'trying to read input file, ',
            'error'         : 'no handler for this cluster type has been derived.',
            'exitCode'      : 10},
        'emailFail'   : {
            'action'        : 'attempting to send notification email, ',
            'error'         : 'sending failed. Perhaps host is not email configured?',
            'exitCode'      : 20},
    }

    def description(self, *args):
        '''
        Get / set internal object description.
        '''
        if len(args):
            self._str_desc = args[0]
        else:
            return self._str_desc

    def log(self): return self._log

    def __init__(self, **kwargs):

        #
        # Object desc block
        #
        self._str_desc                  = ''

        # Directory and filenames
        self._str_workingDir            = ''
        self._str_inputFile             = ''
        self._str_outputFileStem        = ''
        self._str_outputFileType        = ''
        self._str_outputDir             = ''

        self._b_convertAllSlices        = False
        self._sliceToConvert            = -1
        self._frameToConvert            = -1

        self._str_stdout                = ""
        self._str_stderr                = ""
        self._exitCode                  = 0

        # The actual data volume and slice
        # are numpy ndarrays
        self._b_4D                      = False
        self._b_3D                      = False
        self._Vnp_4DVol                 = None
        self._Vnp_3DVol                 = None
        self._Mnp_2Dslice               = None

        # A logger
        self._log                       = msg.Message()
        self._log.syslog(True)

        # Flags
        self._b_showSlices              = False
        self._b_convertMiddleSlice      = False
        self._b_convertMiddleFrame      = False

        for key, value in kwargs.iteritems():
            if key == "inputFile":          self._str_inputFile         = value
            if key == "outputDir":          self._str_outputDir         = value
            if key == "outputFileStem":     self._str_outputFileStem    = value
            if key == "outputFileType":     self._str_outputFileType    = value
            if key == "sliceToConvert":     self._sliceToConvert        = value
            if key == "frameToConvert":     self._frameToConvert        = value
            if key == "showSlices":         self._b_showSlices          = value

        if self._frameToConvert.lower() == 'm':
            self._b_convertMiddleFrame = True
        else:
            self._frameToConvert = int(self._frameToConvert)

        if self._sliceToConvert.lower() == 'm':
            self._b_convertMiddleSlice = True
        else:
            self._sliceToConvert = int(self._sliceToConvert)

        str_fileName, str_fileExtension  = os.path.splitext(self._str_outputFileStem)
        if len(self._str_outputFileType):
            str_fileExtension            = '.%s' % self._str_outputFileType

        if len(str_fileExtension) and not len(self._str_outputFileType):
            self._str_outputFileType     = str_fileExtension

        if not len(self._str_outputFileType) and not len(str_fileExtension):
            self._str_outputFileType     = '.png'

    def run(self):
        '''
        The main 'engine' of the class.
        '''

    def echo(self, *args):
        self._b_echoCmd         = True
        if len(args):
            self._b_echoCmd     = args[0]

    def echoStdOut(self, *args):
        self._b_echoStdOut      = True
        if len(args):
            self._b_echoStdOut  = args[0]

    def stdout(self):
        return self._str_stdout

    def stderr(self):
        return self._str_stderr

    def exitCode(self):
        return self._exitCode

    def echoStdErr(self, *args):
        self._b_echoStdErr      = True
        if len(args):
            self._b_echoStdErr  = args[0]

    def dontRun(self, *args):
        self._b_runCmd          = False
        if len(args):
            self._b_runCmd      = args[0]

    def workingDir(self, *args):
        if len(args):
            self._str_workingDir = args[0]
        else:
            return self._str_workingDir

class med2image_nii(med2image):
    '''
    Sub class that handles NIfTI data.
    '''

    def __init__(self, **kwargs):
        med2image.__init__(self, **kwargs)
        nimg = nib.load(self._str_inputFile)
        data = nimg.get_data()
        if data.ndim == 4:
            self._Vnp_4DVol     = data
            self._b_4D          = True
        if data.ndim == 3:
            self._Vnp_3DVol     = data
            self._b_3D          = True

    def run(self):
        '''
        Runs the NIfTI conversion based on internal state.
        '''

        self._log('About to perform NifTI to %s conversion...\n' %
                  self._str_outputFileType)

        frames     = 1
        frameStart = 0
        frameEnd   = 0

        sliceStart = 0
        sliceEnd   = 0

        if self._b_4D:
            self._log('4D volume detected.\n')
            frames = self._Vnp_4DVol.shape[3]
        if self._b_3D:
            self._log('3D volume detected.\n')

        if self._b_convertMiddleFrame:
            self._frameToConvert = int(frames/2)

        if self._frameToConvert == -1:
            frameEnd    = frames
        else:
            frameStart  = self._frameToConvert
            frameEnd    = self._frameToConvert + 1

        for f in range(frameStart, frameEnd):
            if self._b_4D:
                self._Vnp_3DVol = self._Vnp_4DVol[:,:,:,f]
            slices     = self._Vnp_3DVol.shape[2]
            if self._b_convertMiddleSlice:
                self._sliceToConvert = int(slices/2)

            if self._sliceToConvert == -1:
                sliceEnd    = self._Vnp_3DVol.shape[2]
            else:
                sliceStart  = self._sliceToConvert
                sliceEnd    = self._sliceToConvert + 1

            misc.mkdir(self._str_outputDir)
            for i in range(sliceStart, sliceEnd):
                imslice                 = self._Vnp_3DVol[:,:,i]
                # rotate the slice by 90 for conventional display
                self._Mnp_2Dslice       = np.rot90(imslice)

                if self._b_4D:
                    str_outputFile = '%s/%s-frame%03d-slice%03d.%s' % (
                                                            self._str_outputDir,
                                                            self._str_outputFileStem,
                                                            f, i,
                                                            self._str_outputFileType)
                else:
                    str_outputFile = '%s/%s-slice%03d.%s' % (self._str_outputDir,
                                                            self._str_outputFileStem,
                                                            i,
                                                            self._str_outputFileType)
                self._log('outputfile = %s\n' % str_outputFile)
                pylab.imsave(str_outputFile,
                             self._Mnp_2Dslice,
                             cmap = cm.Greys_r)


def synopsis(ab_shortOnly = False):
    scriptName = os.path.basename(sys.argv[0])
    shortSynopsis =  '''
    SYNOPSIS

            %s                                   \\
                    -i|--input <inputFile>                 \\
                    [-d|--outputDir <outputDir>]           \\
                    -o|--output <outputFileStem>           \\
                    [--outputFileType <outputFileType>]    \\
                    [--sliceToConvert <sliceToConvert>]    \\
                    [--frameToConvert <frameToConvert>]    \\
                    [--showSlices]                         \\
                    [--man|--synopsis]
    ''' % scriptName

    description =  '''
    DESCRIPTION

        `%s' converts input medical image formatted data to a more
        display friendly format.

        Currently understands nifti and dicom.

    ARGS

        -i|--inputFile <inputFile>
        Input file to convert. Typically a DICOM file or a nifti volume.

        [-d|--outputDir <outputDir>]
        The directory to contain the converted output image files.

        -o|--outputFileStem <outputFileStem>
        The output file stem to store conversion. If this is specified
        with an extension, this extension will be used to specify the
        output file type.

        [--outputFileType <outputFileType>]
        The output file type. If different to <outputFileStem> extension,
        will override extension in favour of <outputFileType>.

        [--sliceToConvert <sliceToConvert>]
        In the case of volume files, the slice (z) index to convert. Ignored
        for 2D input data. If a '-1' is sent, then convert *all* the slices.

        [--frameToConvert <sliceToConvert>]
        In the case of 4D volume files, the volume (V) containing the
        slice (z) index to convert. Ignored for 3D input data. If a '-1' is sent,
        then convert *all* the frames.

        [--showSlices]
        If specified, render/show image slices as they are created.

        [--man|--synopsis]
        Show either full help or short synopsis.

    EXAMPLES


    ''' % (scriptName)
    if ab_shortOnly:
        return shortSynopsis
    else:
        return shortSynopsis + description

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="med2view converts an input medical image file to a more conventional graphical format.")
    parser.add_argument("-i", "--inputFile",
                        help="input file",
                        dest='inputFile')
    parser.add_argument("-o", "--outputFileStem",
                        help="output file",
                        dest='outputFileStem')
    parser.add_argument("-d", "--outputDir",
                        help="output image directory",
                        dest='outputDir',
                        default='./')
    parser.add_argument("-t", "--outputFileType",
                        help="output image type",
                        dest='outputFileType',
                        default='none')
    parser.add_argument("-s", "--sliceToConvert",
                        help="slice to convert (for 3D data)",
                        dest='sliceToConvert',
                        default='-1')
    parser.add_argument("-f", "--frameToConvert",
                        help="frame to convert (for 4D data)",
                        dest='frameToConvert',
                        default='-1')
    parser.add_argument("--printElapsedTime",
                        help="print program run time",
                        dest='printElapsedTime',
                        action='store_true',
                        default=False)
    parser.add_argument('--showSlices',
                        help="show slices that are converted",
                        dest='showSlices',
                        action='store_true',
                        default='False')
    parser.add_argument("--man",
                        help="man",
                        dest='man',
                        action='store_true',
                        default=False)
    parser.add_argument("--synopsis",
                        help="short synopsis",
                        dest='synopsis',
                        action='store_true',
                        default=False)
    args = parser.parse_args()

    if args.man or args.synopsis:
        if args.man:
            str_help     = synopsis(False)
        else:
            str_help     = synopsis(True)
        print(str_help)
        sys.exit(1)

    str_fileName, str_fileExtension  = os.path.splitext(args.inputFile)
    b_processNifti       = False
    b_niftiExt           = (str_fileExtension   == '.nii'    or \
                            str_fileExtension   == '.gz')
    if b_niftiExt:
        C_convert     = med2image_nii(
                                inputFile         = args.inputFile,
                                outputDir         = args.outputDir,
                                outputFileStem    = args.outputFileStem,
                                outputFileType    = args.outputFileType,
                                sliceToConvert    = args.sliceToConvert,
                                frameToConvert    = args.frameToConvert,
                                showSlices        = args.showSlices
                            )

    else:
        C_convert   = med2image(
                                inputFile         = args.inputFile,
                                outputFileStem    = args.outputFileStem,
                                outputFileType    = args.outputFileType,
                                sliceToConvert    = args.sliceToConvert
                             )


    # And now run it!
    misc.tic()
    C_convert.run()
    if args.printElapsedTime: print("Elapsed time = %f seconds" % misc.toc())





