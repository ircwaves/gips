import cookielib
import netrc
import urllib2
import re
 
import pydap.lib
from pydap.exceptions import ClientError
 
 
# Set the debug level for urllib2.
debuglevel=1

def install_basic_client(uri='', user='', passwd='', use_netrc=True):
    # Create special opener with support for Cookies
    cj = cookielib.CookieJar()
    
    # Create the password manager and load with the credentials using 
    pwMgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
 
    # Get passwords from the .netrc file nless use_netrc is False    
    if use_netrc:
        logins = netrc.netrc()
        accounts = logins.hosts # a dist of hosts and tuples
        for host, info in accounts.iteritems():
            login, account, password = info
            pwMgr.add_password(None, host, login, password)
        
    if uri and user and passwd:
        pwMgr.add_password(None, uri, user, passwd)
    
    opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(pwMgr),
                                  urllib2.HTTPCookieProcessor(cj))
    
    opener.addheaders = [('User-agent', pydap.lib.USER_AGENT)]
 
    urllib2.install_opener(opener)

    
    def new_request(url):
        # Remove mysterious ampersand, based on GESDISC help response.
        # But why is it there? If it's there, why is it only there sometimes?
        if url[-1] is '&': url = url[0:-1]

        r = urllib2.urlopen(url)            
        resp = r.headers.dict
        resp['status'] = str(r.code)
        data = r.read()
 
        # When an error is returned, we parse the error message from the
        # server and return it in a ``ClientError`` exception.
        if resp.get("content-description") == "dods_error":
            m = re.search('code = (?P<code>\d+);\s*message = "(?P<msg>.*)"',
                    data, re.DOTALL | re.MULTILINE)
            msg = 'Server error %(code)s: "%(msg)s"' % m.groupdict()
            raise ClientError(msg)
 
        return resp, data
 
    from pydap.util import http
    http.request = new_request
