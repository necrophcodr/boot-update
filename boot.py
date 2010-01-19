#!/usr/bin/python2

import os, sys

BLUE="[34;01m"
CYAN="[36;01m"
CYANN="[36m"
GREEN="[32;01m"
RED="[31;01m"
PURP="[35;01m"
OFF="[0m"
version="1.0"

def versinfo():
    print
    print " Copyright "+CYANN+"2010"+OFF+" Funtoo Technologies, LLC."
    print
    print """ This program is free software; you can redistribute and/or modify it under
 the terms of the GNU General Public License version 3 as published by the
 Free Software Foundation. Alternatively you may (at your option) use any
 other license that has been publicly approved for use with this program by
 Funtoo Technologies, LLC. (or its successors, if any.)
 """

if len(sys.argv)>=2 and (( "-v" in sys.argv ) or ( "--version" in sys.argv )):
	versinfo()
	sys.exit(0)

print
print " "+PURP+"boot-update "+OFF+CYANN+version+OFF
print " "+GREEN+"Copyright 2010 Funtoo Technologies."+OFF
print " Use the \"-v\" option to display licensing information."
print

def cleanup(ok,allmsgs):

	warnings = False

	# This is the function that prints all accumulated errors and/or warnings and exits with
	# the proper return code.

	print
	for type, msg in allmsgs:
		if type == "warn":
			print RED+" * WARNING:"+OFF+" %s" % msg
			warnings=True
		elif type == "fatal":
			print RED+" * ERROR:  "+OFF+" %s" % msg
		elif type == "info":
			print GREEN+" * "+OFF+msg
	if not ok:
		print
		print RED+" * Did not complete successfully."+OFF
		print
		sys.exit(1)
	else:
		print
		print GREEN+" * "+OFF+"Completed successfully",
		if warnings:
			print "with warnings."
		else:
			print "."
		print
		sys.exit(0)

# This is only needed for testing from the root of the git repo:
if os.path.isdir(".git") and os.path.basename(os.getcwd()) == "coreboot":
	sys.path.append("python/modules")

# Import Funtoo extensions that we use:

import funtoo.boot.config
import funtoo.boot.helper
import funtoo.boot.extensions

ok=True
allmsgs=[]
cfile="/etc/boot.conf"

# Load /etc/boot.conf master configuration file:

c=funtoo.boot.config.BootConfigFile(cfile)

if not c.fileExists():
	ok=False
	allmsgs.append(["fatal","Master configuration file \"%s\" does not exist." % cfile])
	cleanup(ok,allmsgs)

# Figure out what extension we should be loading...

generate=c["boot/generate"]

if generate=="":
	ok=False
	allmsgs.append(["fatal","boot/generate does not specify a valid boot loader to generate a config for."])

if generate not in funtoo.boot.extensions.__all__:
	ok=False
	allmsgs.append(["fatal","extension for boot loader \"%s\" (specified in boot/generate) not found." % generate ])

if not ok:
	cleanup(ok,allmsgs)

# Dynamically import the proper extension module (ie. grub.py, grub-legacy.py, lilo.py):

extname="funtoo.boot.extensions.%s" % generate
__import__(extname)
extmodule=sys.modules[extname]

# Create Boot Loader Extension object:

def mesg(type,line):
	if type == "info":
		print GREEN+" *"+OFF+" "+line
	elif type == "boot":
		print CYAN+" >>> "+GREEN+line+OFF
	else:
		print RED+" *"+OFF+" "+line

ext=extmodule.getExtension(c)
ext.mesg=mesg

# Before regenerating the config file, we want to auto-mount boot if it isn't already mounted:

imountedit = False

if funtoo.boot.helper.fstabHasEntry("/boot"):
	if not os.path.ismount("/boot"):
		print "Mounting filesystem /boot..."
		os.system("mount /boot")
		imountedit=True
else:
	print "No /etc/fstab entry for /boot; not mounting."


# Regenerate Config File:

step, ok, msgs = ext.regenerate()
allmsgs += msgs

if ok:
	print
	for bootitem in ext.bootitems:
		mesg("boot",bootitem)

# If we mounted /boot, we should unmount it:
if imountedit:
	print
	print "Unmounting /boot"
	os.system("umount /boot")

cleanup(ok,allmsgs)
