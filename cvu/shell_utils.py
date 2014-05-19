#    (C) Roan LaPlante 2013 rlaplant@nmr.mgh.harvard.edu
#
#	 This file is part of cvu, the Connectome Visualization Utility.
#
#    cvu is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from utils import CVUError

def sh_cmd(cmd):
    import subprocess; import os
    with open(os.devnull,'wb') as devnull:
        try:
            subprocess.check_call(cmd,#stdout=devnull,stderr=subprocess.STDOUT,
                shell=True)
        except subprocess.CalledProcessError as e:
            raise CVUError(str(e))	

def sh_cmd_grep(cmd,grep):
    #this function is inspired by a similar function from connectomemapper
    import subprocess; import os; import random; import time; import tempfile
    t=random.randint(1,10000000)
    try: os.mkdir(os.path.join(tempfile.gettempdir(),'cvu'))
    except OSError: pass
    fname=os.path.join(tempfile.gettempdir(),"out_fifo_%s" % str(t))

    try: os.unlink(fname)
    except: pass

    retln=[]
    os.mkfifo(fname)
    try:
        fifo=os.fdopen(os.open(fname,os.O_RDONLY|os.O_NONBLOCK))
        newcmd="( %s ) 1>%s"%(cmd,fname)
        process=subprocess.Popen( newcmd, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE )
        
        while process.returncode == None:
            time.sleep(.5)
            process.poll()
            try:
                ln=fifo.readline().strip()
            except: continue
            if ln and grep in ln:
                retln.append(ln)
        rem=fifo.read()
        if rem:
            for ln in [ln for ln in rem.split('\n') if ln.strip()]:
                if grep in ln:
                    retln.append(ln)
        if process.returncode:
            raise CVUError('%s failed with error code %s' % 
                (cmd,process.returncode))	
    finally:
        try: os.unlink(fname)
        except: pass
        return retln

def sh_cmd_retproc(cmd, debug=False):
    import subprocess; import os
    with open(os.devnull,'wb') as devnull:
        outfd = None if debug else devnull

        process=subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,
            stdout=outfd,stderr=outfd)
        
        #checks to see if the specified command was bad
        if process.poll():
            process.kill()
            raise CVUError('% failed with error code %s' % 
                (cmd,process.returncode))
        return process

def tcsh_env_interpreter(source_fname):
    import subprocess; import os
    
    cmd=['tcsh','-c','source %s && env' % source_fname]

    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=False)
    for ln in proc.stdout:
        ln=ln.strip()
        k,_,v=ln.partition("=")
        os.environ[k]=v

    #proc.communicate()
