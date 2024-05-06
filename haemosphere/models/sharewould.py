
"""\
ShareWould
==========

This module is for applications that *would* like to *share* files among users, groups, or even 
the general public.  (At the time I wrote this I was playing Robin Hood in "Robin Hood's Lament",
and morphed *Sherwood* for the name of this proggy.   Since Sherwood was a forest and forest has
trees, just like this involves directory trees ... get it?  Don't like it?  Sue me.   When you
come right down to it, this is really nothing more than a namespace manager that takes advantage
of some of the underlying filesystem's functions and semantics.

The Problem
-----------

We have an application that must serve collections among users, groups, and also publically.  These are
all static in the sense that, for the purposes of this application, they are read-only.   We wanted a 
simple way to let users publish their collections and still have some control over who else can see them.

The Solution
------------

A file / directory hierarchy is constructed in which collections, taking the form of files, are stored
in subdirectories allocated to individual users.    Users may then publish their collections in other users'
or groups' directories, or in the ''PUBLIC'' directory.   The act of "publishing" involves little more than
the creation of a *symbolic link* in the target directory that points back to the original file. 

Publishing
----------

Since only a user can "own" a publishable file, only a user can publish that file.   Although it is technically
feasible to publish a file in a group and then publish that group's notion (i.e. the symlink) of the file
elsewhere, creating a chain of symlinks, this begins to make managing subscriptions (see next section)
much more difficult, and it also makes control of publication a bit too loose.   Though somewhat artificial, 
publishing is therefore constrained to something only users can do, and they can do it only with files they
"own" -- i.e., that are in their own directory.  If someone in a group to which a file has been publishes wishes 
to have it published elsewhere, they need to get the owner of the file to publish it.

While ShareWould itself won't enforce this, directly, it supports it by not creating the subscription support
structures in the group or public directories; only in private, user directories.

Subscription
------------

Each file in a user's directory has a corresponding ``.sub`` file, which is nothing more than
a TAB-separated (TSV) file containing three columns: a subscriber name (or PUBLIC), a column telling whether this is
published to a private individual (user) or a group, and an alias column used to sort out namespace collisions.

These files are used to keep track of where their corresponding collection files have been published.
Thus, when the collection is removed or re-parented, the symlinks to that file can be removed or updated.
Note that there are NO such files in the public or group directories.  Again, only users can "own" or publish
files.

Permissions
-----------

Since this is intended to be used for collaboration, we're not all that fussed about permissions and who can do what.
The main idea is to keep stuff private that we don't want made public.  The assumption is that if something has
been shard, it was intended to be shared.  If something was mistakenly shared, it can always be un-shared.   

Furthermore, this module, at least in its initial form, did not take part in authorization checks.   If a method
is called, it assumes that the caller had permission to make that call, be it adding, removing, publishing, unpublishing, &c.


"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os, re

import logging
log = logging.getLogger(__name__)

# ----------------------------------------------------------
# module level variables and functions
# ----------------------------------------------------------
rootPath = None
"""2015-12-09. Jarny. Changed the way init_model works. Now it just sets rootPath rather than returning the Sharewould instance.
This makes it more consistent with users.py and also enables module usage more flexible.
"""
def init_model(_rootPath):
	global rootPath
	rootPath = _rootPath
        
def allInventories(sieve='h5'):
	"""Return a list of all inventories (ie. full paths to files), under rootPath. Call after rootPath has been set.
	"""
	inventories = []
	for root, dirs, filenames in os.walk(rootPath):
		for filename in filenames:
			filepath =  os.path.join(root,filename)
			if filename.endswith(sieve) and not os.path.islink(filepath):
				inventories.append(filepath)
	return inventories

# ----------------------------------------------------------
# Main class
# ----------------------------------------------------------
class ShareWould(object):
    """\
Manage a tree of files and directories containing collections to be shared (or not.)

On instantiation a root path may be supplied.  If this path doesn't exist or doesn't contain 
a ShareWould tree, one will be created if ''create_it='' keyward argument is set to ''True''.   Otherwise,
an exception is thrown.
"""
    def __init__(self, root=".", create_it=False):
        
        self._top = os.path.abspath(os.path.join(root, 'F0r3sT'))
        self._public = os.path.join(self._top, 'PUBLIC')
        self._groups = os.path.join(self._top, 'PRIVATE', 'GROUPS')
        self._users = os.path.join(self._top, 'PRIVATE', 'USERS')

        # See if the root of the tree exists.
        if not os.path.exists(self._top):
            
            # Nope.  Should we create it, then?
            if create_it:
                os.makedirs(self._public)
                os.makedirs(self._groups)
                os.makedirs(os.path.join(self._users, 'anonymouse'))
                os.symlink(self._public, os.path.join(self._users, 'PUBLIC'))

            else:
                raise OSError("Can't see the forest for the trees in '{0}'".format(root))

    
    def add(self, username, collection=None):
        """\
Add a user named *username* to the forest, checking to make sure there isn't already one
there by that name.  

If *collection* is specified, a file by that name is opened in the directory and 
a ``file`` instance is returned.  This can then be used to fill the file ... somehow.
"""
        path = os.path.join(self._top, 'PRIVATE', 'USERS', username)
        if not os.path.exists(path):
            os.mkdir(path)

        # If there's a collection, also set up a subscriber file for it
        # to keep track of symlinks to it that will need to be updated
        # if/when the collection is re-parented.
        # Note that we open this in append mode so that if there's already 
        # one present (there really shouldn't be) we don't scrog it.
        if collection is not None:
            ds_path = os.path.join(path, collection)
            open(ds_path + '.sub', 'a').close()  
            return open(ds_path, 'w')

        return None


    def remove(self, username, collection=None, new_parent='anonymouse'):
        """\
Removes the user from the forest.  If the user owns files, re-parent them to
another user, or delete them if no other user specified.

If the collection is specified, just reparent that collection.  If `new_parent` isn't specified,
the collection is reparented to the *anonymous* user.

Throws OSError if collection is specified and is not found in the user directory.
Throws Value error if the use
"""
        path = os.path.join(self._top, 'PRIVATE', 'USERS', username)
        
        if  username == 'anonymouse':   # NEVER remove / reparent these!
            # Just shine the collar on.
            return True

        elif not os.path.exists(path):
            #return True
            raise ValueError("No such user '{0}'".format(username))

        contents = os.listdir(path)
            
        if contents:
            # Are we just removing a collection?
            if collection in contents:
                self.reparent(username, collection, new_parent)
                return True 
                
            else: 
                # Either the directory is empty, or the collection isn't among the ones there.
                # In either case, thsi might be a mistake, so err on the side of caution and
                # do nothing else.
                raise OSError("Collection '{0}' not found in '{1}' or '{1}' is empty".format(collection, username))

            # Looks like we're caning the whole magilla.
            for child in contents:
                self.reparent(username, child, new_parent)

        os.rmdir(path)
        return True


    def reparent(self, current_parent, collection, new_parent='anonymouse'):
        """\
Move the collection from this user to a new parent.
"""
        old_path = os.path.join(self._top, 'PRIVATE', 'USERS', current_parent)
        if not os.path.exists(old_path):
            raise OSError("Source ({0}) doesn't exist".format(current_parent))


        # Update symlinks to it, if any
        subscribers = [ [ x.strip() for x in y.split('\t') ] for y in open(os.path.join(old_path, collection + '.sub'), 'r') ]
        for sub in subscribers:
            if sub[0] == current_parent and sub[1] == 'user': continue
            self.unpublish(current_parent, collection, **{ sub[1]: sub[0] })
            self.publish(collection, new_parent, **{ sub[1]: sub[0] })
            
        # Move the file
        new_path = os.path.join(self._top, 'PRIVATE', 'USERS', new_parent)
        if not os.path.exists(new_path):
            raise OSError("Source ({0}) doesn't exist".format(new_parent))
        os.rename(os.path.join(old_path, collection), os.path.join(new_path, collection) )
        os.unlink(os.path.join(old_path, collection+'.sub'))

        return new_parent

    
    def publish(self, collection, owner, user=None, group=None, alternate=False):
        """\
Publish the collection.   

If neither user nor group are specified, this will make the collection 
public to all.  (Note that this will basically obliterate the .sub file for that collection 
since having other, private subscriptions is non-sensical.)

`user` and `group` specification are otherwise mutually exclusive.  If a ``group=`` keyword
is used, it makes no sense to specify a user, and likewise if a ``user=`` keyword is given.

An `OSError` exception is thrown if the user (or group) specified does not exist.

The name of the published collection is returned on success, ``None`` (or the collection name) if it is already
published at the target, or ``False`` if publication fails.

Namespace Collision
-------------------

If the collection is already published in the target area then one one of two things will happen:

 *if `alternate` is ``False`` the operation will fail and the collection is not published.  ``None`` is returned. 
 * If`alternate` is ``True`` the collection will be published as the specified name with a number suffixed
   to the name.  (e.g. ``myCollection`` becomes ``myCollection.1``.)  A FINITE NUMBER of attempts will be made
   and then utter, abject failure will be declared, and the code will suck itself into a singularity
   along with all the ale on Rigel 7.  So ... be warned.
 * If `alternate is ``None``, publication fails and ``None`` is returned.
 * If `alternate` is a string (or unicode) or a number, this is suffixed to the collection name.
   If this still results in a namespace collision, publication fails and ``None`` is returned.

"""
        # ALL collections are owned by a "private" user, even if that user is anonymouse.
        source = os.path.join(self._top, 'PRIVATE', 'USERS', owner)
        if not os.path.exists(source):
            raise OSError("No such collection '{0}' or user '{1}'".format(collection, user))

        # Can only specify user= or group=, not both.
        if not (user is None or group is None):
            raise TypeError("cannot specify both user= and group= keyword argument")

        elif user is None and group is None:
            ptype, target, target_path = 'user', 'PUBLIC', os.path.join(self._top, 'PUBLIC')

        elif user is None:
            ptype, target, target_path = 'group', group, os.path.join(self._top, 'PRIVATE', 'GROUPS', group)

        elif group is None:
            ptype, target, target_path = 'user', user, os.path.join(self._top, 'PRIVATE', 'USERS', user)
        else:
            raise TypeError('should NEVER get here!')
            
        # Make sure target area exists
        if not os.path.exists(target_path):
            raise OSError("{0} '{1}' does not exist".format(ptype, target))
                
        # Check to see that we have a subscriber file.  Then see if, for whatever reason
        # this subscription is already registered.
        try:
            subscr = [ [ x.strip() for x in y.split('\t') ] for y in open(os.path.join(source, collection + '.sub')) ]
            for sub in subscr:
                if len(sub) < 3: continue   # invalid subscriber record -- skip it

                if tup[0] == target:  # Already published here, or, just accept abject failure!
                    if alternate in [ target, None, False ]:
                        return alternate
                        
                    elif alternate is True:   
                        # Recursivel try to append a numeric suffix (.1, .2 ...) until we get something.
                        # (do we need to limit this?)
                        suffix = 0
                        while suffix < 5:   # C'mon. Do we really need more than 5 with the same friggin' name?  Really!?
                            alternate = self.publish(collection +'.'+str(suffix), owner, **{ ptype: target })  # alternate=False
                            if alternate not in [None, False]:
                                return alternate  # Success!
                            suffix += 1  # Keep trying ...
                            
                        return False # Failure!

                    else:  # alternate is some explicity suffix -- just one try is all we're gonna take
                        return self.publish(collection + '.' + alternate, owner, **{ptype: pub})

            # If we made it here, it hasn't already been published at the specified location
            subscr.append([target, ptype, collection ])

        except:

            subscr = list()

        finally:
            os.symlink(os.path.join(source, collection), os.path.join(target_path, collection))
            open(os.path.join(source, collection + '.sub'), 'a').write("\n".join(['\t'.join([s for s in slines ]) for slines in subscr ])+"\n")
            
        return collection


    def unpublish(self, owner, collection=None, user=None, ignore_errors=True):
        """\
Unpublish collections owned by `owner`.  If a collection is specified, only unpublish that collection.  If
a `user` is specified, only unpublish the collection(s) shared with that user.

If `ignore_errors` is ``False``, an exception will be raised when an error is encountered.
(Probably ``OSError`` due to a collection symlink not actually being there, but ... could be
anything.  Who knows?  Who cares?)

Returns ``True`` if all goes well.
"""
        ds_dir = os.path.join(self._top, 'PRIVATE', 'USERS', owner)
        if not os.path.exists(ds_dir):
            raise OSError("No such user '{0}'".format(owner))
            
        if collection is None:
            subs_files = [ x for x in os.listdir(ds_dir) if x.endswith('.sub') ]

            for ds in subs_files: # Unpublish all collections.
                if self.unpublish(owner, collection=ds, user=user, ignore_errors=ignore_errors) is not True:
                    return False
            
            return True
            
        # If we got here, we are unpublishing a specific collection.
        subscr = [ [ x.strip() for x in y.split('\t') ] for y in open(os.path.join(ds_dir, collection + '.sub')) ]
        
        new_subscr = list()
        for sub in subscr:
            if user in [sub[0], None]:  # Unpublish for this user
                target_path = os.path.join(self._top, 'PRIVATE', 'USERS' if sub[1] == 'user' else 'GROUPS', sub[0], collection)
                if os.path.exists(target_path):
                    os.unlink(target_path)
                elif not ignore_errors:
                    return False
            
            else:
                new_subscr.append(sub)
                
        open(os.path.join(ds_dir, collection + '.sub'), 'w').write("\n".join(['\t'.join([s for s in slines ]) for slines in new_subscr ]))

        return True
            
    def exists(self,  user=None, collection=None):
        """\
Looks for `collection` in the tree, restricting the search only to `user` if specified.
Returns a list of ``(collection, username)`` tuples.  If the collection isn't found anywhere,
the list will, of course, be empty.
"""
        result = list()

        if collection is None and user is None:
            return result

        for subscr in [x for x in os.listdir(os.path.join(self._top, 'PRIVATE', 'USERS')) if (x if x != 'PUBLIC' else None)]:
            if user in [subscr, None]:
                if collection in os.listdir(os.path.join(self._top, 'PRIVATE', 'USERS', subscr)):
                    result.append((subscr, collection))
                elif collection is None:
                    result.append((subscr,))

        return result


    def inventory(self, user, groups=None, sort=True, clean=False, sieve='h5', createDir=True):
        """\
Return a (sorted) list of collection names and handles thereto.   
Remove duplicates from this list where found.  If `sort` is ``False``,
an unsorted list is returned.  If `clean` is ``False``, do not remove duplicates.

NOTE:  The default ``sieve``

Added by jarny, 2015-09-01. user can be None (in which case only public inventories are returned.
Jarny, 2018-06-14: Added createDir argument. If True, will create the user directory path if it doesn't exist,
if False, will raise an exception.
"""
        result = list()
        handles = list()
        if groups is None: groups = list()

        if sieve is None:
            sieve = re.compile(r'.*')

        elif sieve in ('h5', 'gsp', 'sub', 'p'):    # May add others, later
            sieve = re.compile(r'.*\.'+sieve)

        else:
            sieve = re.compile(sieve)

        def addHandle(h, p):
            handle_parts = os.path.splitext(handle)
            if handle_parts[1] == '.sub': return
            if handle_parts[0] in handles and clean == True: return
            result.append((handle_parts[0], os.path.join(p, handle)))
            handles.append(handle_parts[0])

        # Add the public ones.
        for handle in os.listdir(self._public):
            if handle[0] == '.': continue   # Don't show hidden files.
            if sieve.match(handle):
                addHandle(handle, self._public)

        if user:
            # Now iterate through the user's private directory as well.
            path = os.path.join(self._users, user)

            # path doesn't exist and createDir, make it
            if not os.path.exists(path) and createDir:
            	os.mkdir(path)
            	
            for handle in os.listdir(path):
                if handle[0] == '.': continue   # Don't show hidden files.
                if sieve.match(handle):
                    addHandle(handle, path)

            # Include groups if list was provided
            for group in groups:
                path = os.path.join(self._groups, group)
                if not os.path.exists(path): continue	# Can't get inventory from non-existing path
                for handle in os.listdir(path):
                    if handle[0] == '.': continue   # Don't show hidden files.
                    if sieve.match(handle):
                        addHandle(handle, path)
        return sorted(result, key= lambda x: x[0].upper()) if sort else result
        
        
    def picklefile(self, username, obj, filename):
        """\
Added by jarny, 2015-02-05. Use cPickle to dump obj to filename into the directory of user.
Mainly used to store saved genesets. Eg: forest.picklefile('jarny',geneSet,'Kit.p')
"""
        import six.moves.cPickle
        six.moves.cPickle.dump(obj, open(os.path.join(self.directory(username), filename),'w'), -1)

    def loadfile(self, username, filename):
        """\
Added by jarny, 2015-02-05. Use cPickle to read obj from filename under the directory of user and return the object.
Mainly used to retrieve saved genesets. Eg: geneSet = forest.loadfile('jarny','Kit.p')
"""
        import six.moves.cPickle
        import pickle
        filepath = os.path.join(self.directory(username), filename)
        '''

        try:
            with open(filepath, 'rb') as f:
                pickle_data = pickle.load(f)
        except UnicodeDecodeError as e:
            with open(filepath, 'rb') as f:
                pickle_data = pickle.load(f, encoding='latin1')
        except Exception as e:
            print('Unable to load data ', filepath, ':', e)
            raise

        return filepath
        '''
        return six.moves.cPickle.load(open(filepath,'rb', encoding="ascii", errors="backslashreplace")) if os.path.exists(filepath) else None
        #return pickle.load(open(filepath,'rb'), encoding="iso-8859-1") if os.path.exists(filepath) else None
    def directory(self, username):
        """\
Added by jarny, 2016-05-04. Return the directory path of the user.
"""
        return os.path.join(self._top, 'PRIVATE', 'USERS', username)


        
def testit(root='.'):

    print("path doesn't yet exist ... ", end=' ')
    assert not os.path.exists(os.path.join(root, 'F0r3sT'))
    print('pass')

    print('try to open nonexistent share ... ', end=' ')
    try:
        sw = ShareWould(root)  # Should fail
    except OSError:
        print('pass')

    print('try to create non-existent share ... ', end=' ')
    sw = ShareWould(root, create_it=True)
    assert os.path.exists(os.path.join(root, 'F0r3sT'))
    print('pass')

    print('adding a user ... ', end=' ') 
    sw.add('nicks')
    found = sw.exists(user='nicks')
    assert len(found) > 0
    assert found[0][0] == 'nicks'
    print('pass')
    
    print('adding a collection ... ', end=' ') 
    sw.add('nicks', 'hiltonlab')
    found = sw.exists(collection='hiltonlab')
    assert len(found) > 0
    assert found[0][0] == 'nicks' and found[0][1] == 'hiltonlab'
    print('pass')

    print('adding a collection and a user ... ', end=' ')
    sw.add('jarny', 'goodell')
    found = sw.exists(collection='goodell')
    assert len(found) > 0 and found[0][0] == 'jarny'
    print('pass')
    
    print("publish a collection in another user's directory ... ", end=' ')
    assert not os.path.exists('F0r3sT/PRIVATE/USERS/jarny/hiltonlab')
    sw.publish('hiltonlab', 'nicks', user='jarny')
    assert os.path.exists('F0r3sT/PRIVATE/USERS/jarny/hiltonlab')
    print('pass')

    print("unpublish a collection in another user's directory ... ", end=' ')
    assert os.path.exists('F0r3sT/PRIVATE/USERS/jarny/hiltonlab')
    sw.unpublish('nicks', 'hiltonlab', user='jarny')
    assert not os.path.exists('F0r3sT/PRIVATE/USERS/jarny/hiltonlab')
    assert len([x for x in open('F0r3sT/PRIVATE/USERS/nicks/hiltonlab.sub') if (x if x.split('\t')[0] == 'jarny' else None)]) == 0
    print('pass')

    print('reparent a collection ... ', end=' ')
    assert os.path.exists('F0r3sT/PRIVATE/USERS/nicks/hiltonlab') and not os.path.exists('F0r3sT/PRIVATE/USERS/jarny/hiltonlab')
    sw.reparent('nicks', 'hiltonlab', 'jarny')
    assert (not os.path.exists('F0r3sT/PRIVATE/USERS/nicks/hiltonlab')) and os.path.exists('F0r3sT/PRIVATE/USERS/jarny/hiltonlab')
    print('pass')

    print("publish a collection in another user's directory ... ", end=' ')
    assert not os.path.exists('F0r3sT/PRIVATE/USERS/nicks/hiltonlab')
    sw.publish('hiltonlab', 'jarny', user='nicks')
    assert os.path.exists('F0r3sT/PRIVATE/USERS/nicks/hiltonlab')
    print('pass')

    print('list what this user can see ... ', end=' ')
    j_inv = sw.inventory('jarny')
    n_inv = sw.inventory('nicks')
    assert len(j_inv) == 2 and sorted([x[0] for x in j_inv]) == ['goodell', 'hiltonlab']
    assert len(n_inv) == 1 and n_inv[0][0] == 'hiltonlab'
    print('(pass)')

    print('add collection to users directory and make it public ... ', end=' ')
    sw.add('nicks', 'anotherCollection')
    sw.publish('anotherCollection', 'nicks')
    #print sw.inventory('nicks')
    assert os.path.exists('F0r3sT/PUBLIC/anotherDataset')
    print(' pass')

    os.system('rm -rf ' + os.path.join(root, 'F0r3sT'))
    print('All tests passed')
    
    
if __name__ == '__main__':
    import sys
    testit('.' if len(sys.argv) < 2 else sys.argv[1])
                          
