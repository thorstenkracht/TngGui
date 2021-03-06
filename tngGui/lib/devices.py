#!/usr/bin/env python
'''
the class Devices reads online.xml and creates lists for the various
device types. For motors and MGs it also looks into the Pool. 

'''
import json, os, time
import HasyUtils
import PyTango
#
# list those modules that have the attribite widget prepared
#
cameraNames = ['dalsa', 'eigerdectris',  
               'lambda','pilatus100k', 'pilatus300k', 'pilatus1m', 'pilatus2m', 'pilatus6m']

PiLCModuleNames = ['pilc_module']

modulesRoiCounters = ['mca8715roi', 
                      'vortex_roi1', 'vortex_roi2', 'vortex_roi3', 'vortex_roi4', 
                      'amptekroi',
                      'mythenroi']

def matchTags( dev, cliTags): 
    '''
    tags <tags>user</tags> 
    cliTags -t user,expert
    '''
    lstTags = dev[ 'tags'].split( ',')

    if cliTags:
        if type( cliTags) is list: 
            if len( cliTags) == 1: 
                lstCliTags = cliTags[0].split( ',')
            else: 
                lstCliTags = cliTags
        else: 
            lstCliTags = cliTags.split( ',')
        lstCliTags = [ elm.strip() for elm in lstCliTags]
    else:
        lstCliTags = None

    for tag in lstTags: 
        for cliTag in lstCliTags: 
            if tag.upper() == cliTag.upper():
                print( "devices.matchTags: %s tags %s vs. cliTags %s, return True " % ( dev[ 'name'], repr( dev[ 'tags']), repr( lstCliTags)))
                return True
    print( "devices.matchTags: %s tags %s vs. cliTags %s, return False " % ( dev[ 'name'],repr( dev[ 'tags']), repr( lstCliTags)))
    return False

class Devices(): 
    def __init__( self, args = None, xmlFile = None, parent = None):
        self.allDevices = []
        self.allDevicesRaw = []  # ignore tags
        self.allMotors = []
        self.allIRegs = []
        self.allORegs = []
        self.allAdcs = []
        self.allMCAs = []
        self.allVfcAdcs = []
        self.allCameras = [] 
        self.allPiLCModules = []
        self.allModuleTangos = []
        self.allDacs = []
        self.allTimers = []
        self.allCounters = []        # sis3820
        self.allTangoAttrCtrls = []
        self.allTangoCounters = []   # VcExecutors
        self.allMGs = []
        self.allDoors = []
        self.allMSs = []
        self.allPools = []
        self.allNXSConfigServer = []

        self.args = args
        if xmlFile is None: 
            self.xmlFile = "/online_dir/online.xml"
        else: 
            self.xmlFile = xmlFile
        #
        # for non motors we don't get devices from the pool, 
        # so use the tags already here
        #
        if self.args is not None: 
            self.allDevices = HasyUtils.getOnlineXML( xmlFile = self.xmlFile, cliTags = self.args.tags)
            self.allDevicesRaw = HasyUtils.getOnlineXML( xmlFile = self.xmlFile)
        else: 
            self.allDevices = HasyUtils.getOnlineXML( xmlFile = self.xmlFile)
            self.allDevicesRaw = self.allDevices

        if self.allDevices is None: 
            raise ValueError( "Devices.__init__: no devices found")

        self.findAllMotors( )
        self.findAllIORegs()
        self.findAllAdcDacs()
        self.findAllMCAs()
        self.findAllCameras()
        self.findAllPiLCModules()
        self.findAllModuleTangos()
        self.findAllTimers()
        self.findAllCounters()
        self.findAllMGs()
        self.findAllDoors()
        self.findAllMSs()
        self.findAllPools()
        self.findAllNXSConfigServer()


        timerName = None
        counterName = None
        if self.args is not None and self.args.counterName:
            counterName = self.args.counterName
        if self.args is not None and self.args.timerName:
            timerName = self.args.timerName

        self.timerName = timerName
        self.counterName = counterName

        return 

    def showAllDevices( self): 
        '''
        display what we have
        '''
        import tempfile, sys

        tempBuffer = ""

        if len( self.allMotors) == 0:
            tempBuffer +=  "No motors\n"
        else: 
            tempBuffer +=  "Motors, %d\n" % len( self.allMotors)
            for dev in self.allMotors: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allIRegs) == 0:
            tempBuffer +=  "No IRegs\n"
        else: 
            tempBuffer +=  "IRegs, %d\n" % len( self.allIRegs)
            for dev in self.allIRegs: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allORegs) == 0:
            tempBuffer +=  "No ORegs\n"
        else: 
            tempBuffer +=  "Oregs, %d\n"  % len( self.allORegs)
            for dev in self.allORegs: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allAdcs) == 0:
            tempBuffer +=  "No ADCs\n"
        else: 
            tempBuffer +=  "Adcs, %d\n"  % len( self.allAdcs)
            for dev in self.allAdcs: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allMCAs) == 0:
            tempBuffer +=  "No MCAs\n"
        else: 
            tempBuffer +=  "Mcas, %d\n" % len( self.allMCAs)
            for dev in self.allMCAs: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allVfcAdcs) == 0:
            tempBuffer +=  "No VfcAdcs\n"
        else: 
            tempBuffer +=  "VfcAdcs, %d\n" % len( self.allVfcAdcs)
            for dev in self.allVfcAdcs: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allCameras) == 0:
            tempBuffer +=  "No Cameras\n"
        else: 
            tempBuffer +=  "Cameras, %d\n" % len( self.allCameras)
            for dev in self.allCameras: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allPiLCModules) == 0:
            tempBuffer +=  "No PiLCModules\n"
        else: 
            tempBuffer +=  "PiLCModules, %d\n" % len( self.allPiLCModules)
            for dev in self.allPiLCModules: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allModuleTangos) == 0:
            tempBuffer +=  "No ModuelTangos\n"
        else: 
            tempBuffer +=  "ModuleTangos, %d\n" % len( self.allModuleTangos)
            for dev in self.allModuleTangos: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allDacs) == 0:
            tempBuffer +=  "No DACs\n"
        else: 
            tempBuffer +=  "Dacs, %d\n" % len( self.allDacs)
            for dev in self.allDacs: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allTimers) == 0:
            tempBuffer +=  "No Timers\n"
        else: 
            tempBuffer +=  "Timers, %d\n" % len( self.allTimers)
            for dev in self.allTimers: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allCounters) == 0:
            tempBuffer +=  "No Counters\n"
        else: 
            tempBuffer +=  "Counters, %d\n" % len( self.allCounters)
            for dev in self.allCounters: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allTangoAttrCtrls) == 0:
            tempBuffer +=  "No TangoAttrCtrls\n"
        else: 
            tempBuffer +=  "TangoAttrCtrls, %d\n" % len( self.allTangoAttrCtrls)
            for dev in self.allTangoAttrCtrls: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allTangoCounters) == 0:
            tempBuffer +=  "No Counters\n"
        else: 
            tempBuffer +=  "TangoCounters, %d\n"  % len( self.allTangoCounters)
            for dev in self.allTangoCounters: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allMGs) == 0:
            tempBuffer +=  "No MGs\n"
        else: 
            tempBuffer +=  "MGs, %d\n" % len( self.allMGs)
            for dev in self.allMGs: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allDoors) == 0:
            tempBuffer +=  "No Doors\n"
        else: 
            tempBuffer +=  "Doors, %d\n" % len( self.allDoors)
            for dev in self.allDoors: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allMSs) == 0:
            tempBuffer +=  "No MSs\n"
        else: 
            tempBuffer +=  "MSs, %d\n" % len( self.allMSs)
            for dev in self.allMSs: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allPools) == 0:
            tempBuffer +=  "No Pools\n"
        else: 
            tempBuffer +=  "Pools, %d\n" % len( self.allPools)
            for dev in self.allPools: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        if len( self.allNXSConfigServer) == 0:
            tempBuffer +=  "No NXSConfigServer\n"
        else: 
            tempBuffer +=  "NXSConfigServer, %d\n"  % len( self.allNXSConfigServer)
            for dev in self.allNXSConfigServer: 
                tempBuffer +=  "  %s\n" % dev[ 'name']

        new_file, filename = tempfile.mkstemp()
        if sys.version.split( '.')[0] == '2': 
            os.write(new_file, "#\n%s" % str( tempBuffer))
        else: 
            os.write(new_file, bytes( "#\n%s" % str( tempBuffer), 'utf-8'))
        os.close(new_file)

        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s %s&" % (editor, filename))
        return 
        
    def nameInOnlineXml( self, name): 
        #
        # devices that are in online.xml are not included via the pool
        #
        for dev in self.allDevicesRaw:
            if name == dev[ 'name']:
                return True
        return False

    def rejectedByTags( self, dev): 
        #
        # append a device, if there are no cliTags or there are matching tags
        #
        if self.args is not None and self.args.tags is not None: 
            if 'tags' not in dev: 
                return True
            if not matchTags( dev, self.args.tags):
                return True
        return False

    def findAllMotors( self):
        #
        # read /online_dir/online.xml here because it is also elsewhere
        #
        #{'control': 'tango', 
        # 'name': 'd1_mot65', 
        # 'tags': 'user,expert',
        # 'hostname': 'haso107d1:10000', 
        # 'module': 'oms58', 
        # 'device': 'p09/motor/d1.65', 
        # 'type': 'stepping_motor', 
        # 'channel': '65'}
        #
        #
        # find the motors and match the tags
        #
        self.allMotors = []

        if self.allDevicesRaw:
            for dev in self.allDevicesRaw:
                if 'sardananame' in dev:
                    dev[ 'name'] = dev[ 'sardananame']

                if self.rejectedByTags( dev):
                    continue

                if (dev['module'].lower() != 'motor_tango' and 
                    dev['type'].lower() != 'stepping_motor' and
                    dev['type'].lower() != 'dac'):
                    continue
                #
                # if a namePattern is supplied on the command line, 
                # the motor name has to match
                #
                if self.args is not None and \
                   self.args.namePattern is not None and \
                   len( self.args.namePattern) > 0: 
                    flagReject = True
                    for mot in self.args.namePattern:
                        if HasyUtils.match( dev['name'], mot):
                            #
                            # do not create doubvle entries in allMotors, 
                            # remember this selection: m3y m3yaw m3_dmy05 m3_dmy06
                            # m3y matches m3y AND m3yaw
                            #
                            flagReject = False
                            for devTemp in self.allMotors:
                                if dev['name'] == devTemp[ 'name']:
                                    flagReject = True
                    if flagReject: 
                        continue

                #
                # try to create a proxy. If this is not possible, ignore the motor
                #
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    continue
                dev[ 'flagPseudoMotor'] = False
                dev[ 'flagPoolMotor'] = False
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                self.allMotors.append( dev)
                        
        #
        # there are PseudoMotors that do not appear in online.xml, 
        # e.g. the diffractometer motors. they should also be included
        #
        localPools = HasyUtils.getLocalPoolNames()
        if len( localPools) == 0:
            self.allMotors = sorted( self.allMotors, key=lambda k: k['name'])
            return 
        
        pool = PyTango.DeviceProxy( localPools[0])
        poolMotors = []
        if pool.MotorList is None: 
            self.allMotors = sorted( self.allMotors, key=lambda k: k['name'])
            return 

        for mot in pool.MotorList:
            poolDct = json.loads( mot)
            name = poolDct['name']
            #
            # devices that are in online.xml are not included via the pool
            #
            if self.nameInOnlineXml( name): 
                continue

            #
            # if a namePattern is supplied on the command line, 
            # the motor name has to match
            #
            if self.args is not None and \
               self.args.namePattern is not None and \
               len( self.args.namePattern) > 0: 
                flagReject = True
                for mot in self.args.namePattern:
                    if HasyUtils.match( dev['name'], mot):
                        #
                        # do not create doubvle entries in allMotors, 
                        # remember this selection: m3y m3yaw m3_dmy05 m3_dmy06
                        # m3y matches m3y AND m3yaw
                        #
                        flagReject = False
                        for devTemp in self.allMotors:
                            if dev['name'] == devTemp[ 'name']:
                                flagReject = True
                if flagReject: 
                    continue

            #print( "name NOT in motorDict %s \n %s" % (name, repr( poolDct)))
            #
            # source: haso107d1:10000/pm/e6cctrl/1/Position
            #
            dev = {}
            dev[ 'name'] = name
            dev[ 'type'] = 'type_tango'
            dev[ 'module'] = 'motor_pool'
            dev[ 'control'] = 'tango'
            #
            # source: haso107d1:10000/pm/e6cctrl/1/Position
            #         tango://haspe212oh.desy.de:10000/motor/dummy_mot_ctrl/1
            #
            src = poolDct[ 'source']
            if src.find( "tango://") == 0:
                src = src[ 8:]
            lst = src.split( '/')
            dev[ 'hostname'] = lst[0]
            
            dev[ 'device'] = "/".join( lst[1:-1])
            dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
            dev[ 'flagPoolMotor'] = True
            dev[ 'flagOffline'] = False # devices not responding are flagged offline
            if poolDct[ 'type'] == 'PseudoMotor':
                dev[ 'flagPseudoMotor'] = True
            else:
                dev[ 'flagPseudoMotor'] = False   # exp_dmy01, mu, chi

            dev[ 'proxy'] = createProxy( dev)
            if dev[ 'proxy'] is None:
                continue
            poolMotors.append( dev)

        for dev in poolMotors: 
            self.allMotors.append( dev)

        self.allMotors = sorted( self.allMotors, key=lambda k: k['name'])
        return 

    def findAllIORegs( self):
        #
        # read /online_dir/online.xml here because it is also elsewhere
        #
        #{'control': 'tango', 
        # 'name': 'd1_mot65', 
        # 'hostname': 'haso107d1:10000', 
        # 'module': 'oms58', 
        # 'device': 'p09/motor/d1.65', 
        # 'type': 'stepping_motor', 
        # 'channel': '65'}
        #

        self.allIRegs = []
        self.allORegs = []
        if self.allDevices:
            for dev in self.allDevices:
                if 'sardananame' in dev:
                    dev[ 'name'] = dev[ 'sardananame']

                #
                # append a device, if there are no cliTags or there are matching tags
                #
                if self.args is not None and self.args.tags is not None: 
                    if 'tags' not in dev: 
                        continue
                    if not matchTags( dev, self.args.tags):
                        continue

                if (dev['type'].lower() == 'input_register'):
                    dev[ 'proxy'] = createProxy( dev)
                    if dev[ 'proxy'] is None:
                        print( "findAllIORegs: No proxy to %s, ignoring this device" % dev[ 'name'])
                        continue
                    dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                    dev[ 'flagOffline'] = False # devices not responding are flagged offline
                    self.allIRegs.append( dev)

                if (dev['type'].lower() == 'output_register'):
                    dev[ 'proxy'] = createProxy( dev)
                    if dev[ 'proxy'] is None:
                        print( "findIORegs: No proxy to %s, ignoring this device" % dev[ 'name'])
                        continue
                    dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                    dev[ 'flagOffline'] = False # devices not responding are flagged offline
                    self.allORegs.append( dev)
        
        self.allIRegs = sorted( self.allIRegs, key=lambda k: k['name'])
        self.allORegs = sorted( self.allORegs, key=lambda k: k['name'])
        return 

    def findAllAdcDacs( self):
        #
        # read /online_dir/online.xml here because it is also elsewhere
        #
        # <device>
        # <name>d1_adc01</name>
        # <type>adc</type>
        # <module>tip850adc</module>
        # <device>p09/tip850adc/d1.01</device>
        # <control>tango</control>
        # <hostname>haso107d1:10000</hostname>
        # <channel>1</channel>
        # </device>
        #
        # for non motors we don't get devices from the pool, 
        # so use the tags already here
        #

        self.allAdcs = []
        self.allVfcAdcs = []
        self.allDacs = []
        if self.allDevices:
            for dev in self.allDevices:
                if 'sardananame' in dev:
                    dev[ 'name'] = dev[ 'sardananame']

                #
                # append a device, if there are no cliTags or there are matching tags
                #
                if self.args is not None and self.args.tags is not None: 
                    if 'tags' not in dev: 
                        continue
                    if not matchTags( dev, self.args.tags):
                        continue

                if (dev['module'].lower() == 'tip830' or \
                    dev['module'].lower() == 'tip850adc'):
                    dev[ 'proxy'] = createProxy( dev)
                    if dev[ 'proxy'] is None:
                        print( "findAllAdcDacs: No proxy to %s, ignoring this device" % dev[ 'name'])
                        continue
                    dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                    dev[ 'flagOffline'] = False # devices not responding are flagged offline
                    self.allAdcs.append( dev)

                if (dev['module'].lower() == 'vfcadc'):
                    dev[ 'proxy'] = createProxy( dev)
                    if dev[ 'proxy'] is None:
                        print( "findAllAdcDacs: No proxy to %s, ignoring this device" % dev[ 'name'])
                        continue
                    dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                    dev[ 'flagOffline'] = False # devices not responding are flagged offline
                    self.allVfcAdcs.append( dev)

                if (dev['module'].lower() == 'tip551' or \
                    dev['module'].lower() == 'tip850dac'):
                    dev[ 'proxy'] = createProxy( dev)
                    if dev[ 'proxy'] is None:
                        print( "findAdcDacs: No proxy to %s, ignoring this device" % dev[ 'name'])
                        continue
                    dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                    dev[ 'flagOffline'] = False # devices not responding are flagged offline
                    self.allDacs.append( dev)
        
        self.allAdcs = sorted( self.allAdcs, key=lambda k: k['name'])
        self.allVfcAdcs = sorted( self.allVfcAdcs, key=lambda k: k['name'])
        self.allDacss = sorted( self.allDacs, key=lambda k: k['name'])
        return 

    def findAllMCAs( self):
        #
        # read /online_dir/online.xml here because it is also elsewhere
        #
        #
        # <device>
        # <name>d1_mca01</name>
        # <type>mca</type>
        # <module>mca_8701</module>
        # <device>p09/mca/d1.01</device>
        # <control>tango</control>
        # <hostname>haso107d1:10000</hostname>
        # <channel>1</channel>
        # </device>
        #
        #
        # for non motors we don't get devices from the pool, 
        # so use the tags already here
        #
        self.allMCAs = []
        for dev in self.allDevices:
            if 'sardananame' in dev:
                dev[ 'name'] = dev[ 'sardananame']

            #
            # append a device, if there are no cliTags or there are matching tags
            #
            if self.args is not None and self.args.tags is not None: 
                if 'tags' not in dev: 
                    continue
                if not matchTags( dev, self.args.tags):
                    continue

            if (dev['module'].lower() == 'mca_8701'):
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print( "findMCAs: No proxy to %s, ignoring this device" % dev[ 'name'])
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                self.allMCAs.append( dev)
        
        self.allMCAs = sorted( self.allMCAs, key=lambda k: k['name'])
        return 

    def findAllCameras( self):
        #
        # read /online_dir/online.xml here because it is also elsewhere
        #
        #
        # <device>
        # <name>lmbd</name>
        # <sardananame>lmbd</sardananame>
        # <type>DETECTOR</type>
        # <module>lambda</module>
        # <device>p23/lambda/01</device>
        # <control>tango</control>
        # <hostname>hasep23oh:10000</hostname>
        # </device>
        #
        self.allCameras = []
        for dev in self.allDevices:
            if 'sardananame' in dev:
                dev[ 'name'] = dev[ 'sardananame']

            #
            # append a device, if there are no cliTags or there are matching tags
            #
            if self.args is not None and self.args.tags is not None: 
                if 'tags' not in dev: 
                    continue
                if not matchTags( dev, self.args.tags):
                    continue

            if dev['module'].lower() in cameraNames: 
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print( "findCameras: No proxy to %s, ignoring this device" % dev[ 'name'])
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                self.allCameras.append( dev)
        
        self.allCameras = sorted( self.allCameras, key=lambda k: k['name'])
        return 

    def findAllPiLCModules( self):
        allPiLCModules = []
        for dev in self.allDevices:
            if 'sardananame' in dev:
                dev[ 'name'] = dev[ 'sardananame']

            #
            # append a device, if there are no cliTags or there are matching tags
            #
            if self.args is not None and self.args.tags is not None: 
                if 'tags' not in dev: 
                    continue
                if not matchTags( dev, self.args.tags):
                    continue

            if dev['module'].lower() in PiLCModuleNames: 
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print( "findPiLCModules: No proxy to %s, ignoring this device" % dev[ 'name'])
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                self.allPiLCModules.append( dev)
        
        self.allPiLCModules = sorted( self.allPiLCModules, key=lambda k: k['name'])
        return 

    def findAllModuleTangos( self):
        #
        # find the motors and match the tags
        #
        self.allModuleTangos = []
        for dev in self.allDevices:
            if 'sardananame' in dev:
                dev[ 'name'] = dev[ 'sardananame']

            #
            # append a device, if there are no cliTags or there are matching tags
            #
            if self.args is not None and self.args.tags is not None: 
                if 'tags' not in dev: 
                    continue
                if not matchTags( dev, self.args.tags):
                    continue

            if dev['module'].lower() == 'module_tango':
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print( "findModuleTangos: No proxy to %s, ignoring this device" % dev[ 'name'])
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                self.allModuleTangos.append( dev)
        
        self.allModuleTangos = sorted( self.allModuleTangos, key=lambda k: k['name'])
        return 

    def findAllMGs( self):
        self.allMGs = []
        for dev in self.allDevices:
            if 'sardananame' in dev:
                dev[ 'name'] = dev[ 'sardananame']

            if self.rejectedByTags( dev):
                continue

            if dev['type'].lower() == 'measurement_group':
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print( "findAllMGs: No proxy to %s, ignoring this device" % dev[ 'name'])
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                self.allMGs.append( dev)
        

        mgAliases = HasyUtils.getMgAliases()
        if mgAliases is None: 
            self.allMGs = sorted( self.allMGs, key=lambda k: k['name'])
            return 

        for mg in mgAliases:
            flag = False
            #
            # see which group we already have
            #
            for dev in self.allMGs:
                if mg.lower() == dev[ 'name']:
                    flag = True
                    break
            if flag: 
                continue

            if self.nameInOnlineXml( mg): 
                continue

            dev = {}
            dev[ 'name'] = mg.lower()
            dev[ 'device'] = 'None'
            dev[ 'module'] = 'None'
            dev[ 'type'] = 'measurement_group'
            dev[ 'hostname'] = "%s" % os.getenv( "TANGO_HOST")
            dev[ 'proxy'] = createProxy( dev)
            if dev[ 'proxy'] is None:
                print( "findAllMGs: No proxy to %s, ignoring this device" % dev[ 'name'])
                continue
            print( "tngGuiClass.Devices.findAllMGs: %s is in the Pool, not in %s" % (dev[ 'name'], self.xmlFile))
            self.allMGs.append( dev)

        self.allMGs = sorted( self.allMGs, key=lambda k: k['name'])
        return 


    def findAllDoors( self):
        self.allDoors = []
        for door in HasyUtils.getDoorNames():
            dev = {}
            dev[ 'name'] = door
            dev[ 'device'] = door
            dev[ 'type'] = "door"
            dev[ 'module'] = "door"
            dev[ 'hostname'] = "%s" % os.getenv( "TANGO_HOST")
            dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
            dev[ 'proxy'] = createProxy( dev)
            self.allDoors.append( dev)

        self.allDoors = sorted( self.allDoors, key=lambda k: k['name'])
        return 

    def findAllMSs( self):
        self.allMSs = []
        for elm in HasyUtils.getMacroServerNames():
            dev = {}
            dev[ 'name'] = elm
            dev[ 'device'] = elm
            dev[ 'type'] = "macroserver"
            dev[ 'module'] = "macroserver"
            dev[ 'hostname'] = "%s" % os.getenv( "TANGO_HOST")
            dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
            dev[ 'proxy'] = createProxy( dev)
            self.allMSs.append( dev)

        self.allMSs = sorted( self.allMSs, key=lambda k: k['name'])
        return 

    def findAllPools( self):
        self.allPools = []
        for elm in HasyUtils.getPoolNames():
            dev = {}
            dev[ 'name'] = elm
            dev[ 'device'] = elm
            dev[ 'type'] = "pool"
            dev[ 'module'] = "pool"
            dev[ 'hostname'] = "%s" % os.getenv( "TANGO_HOST")
            dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
            dev[ 'proxy'] = createProxy( dev)
            self.allPools.append( dev)

        self.allPools = sorted( self.allPools, key=lambda k: k['name'])
        return 

    def findAllNXSConfigServer( self):
        self.allNXSConfigServer = []
        for elm in HasyUtils.getDeviceNamesByClass( "NXSConfigServer"): 
            dev = {}
            dev[ 'name'] = elm
            dev[ 'device'] = elm
            dev[ 'type'] = "nxsconfigserver"
            dev[ 'module'] = "nxsconfigserver"
            dev[ 'hostname'] = "%s" % os.getenv( "TANGO_HOST")
            dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
            dev[ 'proxy'] = createProxy( dev)
            self.allNXSConfigServer.append( dev)

        self.allNXSConfigServer = sorted( self.allNXSConfigServer, key=lambda k: k['name'])
        return 

    def findAllCounters( self):
        #
        # read /online_dir/online.xml here because it is also elsewhere
        #
        # <device>
        # <name>d1_c01</name>
        # <type>counter</type>
        # <module>sis3820</module>
        # <device>p09/counter/d1.01</device>
        # <control>tango</control>
        # <hostname>haso107d1:10000</hostname>
        # <channel>1</channel>
        # </device>
        #
        self.allCounters = []
        self.allTangoCounters = []
        self.allTangoAttrCtrls = []
        if self.allDevices:
            for dev in self.allDevices:
                if 'sardananame' in dev:
                    dev[ 'name'] = dev[ 'sardananame']

                #
                # append a device, if there are no cliTags or there are matching tags
                #

                if self.args is not None and self.args.tags is not None: 
                    if 'tags' not in dev: 
                        continue
                    if not matchTags( dev, self.args.tags):
                        continue

                if (dev['module'].lower() == 'tangoattributectctrl'):
                    dev[ 'proxy'] = createProxy( dev)
                    if dev[ 'proxy'] is None:
                        continue
                    dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                    dev[ 'flagOffline'] = False # devices not responding are flagged offline
                    self.allTangoAttrCtrls.append( dev)
                elif (dev['module'].lower() == 'counter_tango'):
                    dev[ 'proxy'] = createProxy( dev)
                    if dev[ 'proxy'] is None:
                        continue
                    dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                    dev[ 'flagOffline'] = False # devices not responding are flagged offline
                    self.allTangoCounters.append( dev)
                elif dev['module'].lower() in modulesRoiCounters:
                    dev[ 'proxy'] = createProxy( dev)
                    if dev[ 'proxy'] is None:
                        continue
                    dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                    dev[ 'flagOffline'] = False # devices not responding are flagged offline
                    self.allTangoCounters.append( dev)
                elif (dev['type'].lower() == 'counter'):
                    dev[ 'proxy'] = createProxy( dev)
                    if dev[ 'proxy'] is None:
                        continue
                    dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                    dev[ 'flagOffline'] = False # devices not responding are flagged offline
                    self.allCounters.append( dev)

        self.allCounters = sorted( self.allCounters, key=lambda k: k['name'])

        self.allTangoAttrCtrls = sorted( self.allTangoAttrCtrls, key=lambda k: k['name'])
        self.allTangoCounters = sorted( self.allTangoCounters, key=lambda k: k['name'])
        return 

    def findAllTimers( self):
        #
        # read /online_dir/online.xml here because it is also elsewhere
        #
        # <device>
        # <name>d1_t01</name>
        # <type>timer</type>
        # <module>dgg2</module>
        # <device>p09/dgg2/d1.01</device>
        # <control>tango</control>
        # <hostname>haso107d1:10000</hostname>
        # <channel>1</channel>
        # </device>
        #
        self.allTimers = []
        if self.allDevices:
            for dev in self.allDevices:
                if 'sardananame' in dev:
                    dev[ 'name'] = dev[ 'sardananame']

                #
                # append a device, if there are no cliTags or there are matching tags
                #
                if self.args is not None and self.args.tags is not None: 
                    if 'tags' not in dev: 
                        continue
                    if not matchTags( dev, self.args.tags):
                        continue

                if (dev['type'].lower() == 'timer'):
                    dev[ 'proxy'] = createProxy( dev)
                    if dev[ 'proxy'] is None:
                        print( "findAllTimers: No proxy to %s, ignoring this device" % dev[ 'name'])
                        continue
                    dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                    dev[ 'flagOffline'] = False # devices not responding are flagged offline
                    self.allTimers.append( dev)
        
        self.allTimers = sorted( self.allTimers, key=lambda k: k['name'])
        return 


def createProxy( dev):

    try:
        #print( "devices.createProxy %s/%s, %s" % (dev[ 'hostname'], dev[ 'device'], dev[ 'name']))
        #
        #  <device>p08/sis3302/exp.01/1</device>
        #
        if (len( dev[ 'device'].split('/')) == 4 or 
            dev[ 'module'].lower() == 'tangoattributectctrl' or 
            dev[ 'type'].lower() == 'measurement_group'):
            proxy = PyTango.DeviceProxy(  "%s" % (dev[ 'name']))
        else:
            proxy = PyTango.DeviceProxy(  "%s/%s" % (dev[ 'hostname'], dev[ 'device']))
        #
        # state() generates an exception, to see whether the server is actually running
        #
        startTime = time.time()
        sts = proxy.state() 
    except Exception as e:
        print( "tngGui.lib.devices.createProxy: no proxy to %s, flagging 'offline' " % dev[ 'name']   )
        dev[ 'flagOffline'] = True
        for arg in e.args:
            if hasattr( arg, 'desc'):
                print( " desc:   %s" % arg.desc )
        #        print( " origin: %s" % arg.origin)
        #        print( " reason: %s" % arg.reason)
        #        print( "")
            else:
                print( repr( e))
        proxy = None

    return proxy
