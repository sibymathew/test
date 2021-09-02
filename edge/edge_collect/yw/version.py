"""
Handle the version information here; you should only have to
change the version tuple.

Since we are using Docker implementation, we can't  query
the git version as well using the local .entries file.
"""
"""
This version is largely extended with VFD implementation, targeting Series 3, Series 4
Implemented various Serial classes and interfaces are customized to read custom registers
Performance is hugely boosted with decoders using numpy universal functions - to support 500 ms read request per VFD
"""
class Version(object):

    def __init__(self, package, major, minor, micro, pre=None):
        """


        """
        self.package = package
        self.major = major
        self.minor = minor
        self.micro = micro
        self.pre = pre

    def short(self):
        """ Return a string in canonical short version format
        <major>.<minor>.<micro>.<pre>
        """
        if self.pre:
            return '%d.%d.%d.%s' % (self.major, self.minor, self.micro, self.pre)
        else:
            return '%d.%d.%d' % (self.major, self.minor, self.micro)

    def __str__(self):
        """ Returns a string representation of the object

        :returns: A string representation of this object
        """
        return '[%s, version %s]' % (self.package, self.short())


version = Version('yw', 2, 5, 2)

version.__name__ = 'yw'  # fix epydoc error

# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #

__all__ = ["version"]
