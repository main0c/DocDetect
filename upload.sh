piPath="pi@192.168.2.116:/home/pi/test/untitled1"
sourcePath="./"
scp ${sourcePath}/controller.py $piPath/controller.py
scp ${sourcePath}/DetectManager.py $piPath/DetectManager.py
scp ${sourcePath}/GPIODetect.py $piPath/GPIODetect.py
scp ${sourcePath}/repeat.py $piPath/repeat.py
scp ${sourcePath}/gui/BeaconUI.py $piPath/gui/BeaconUI.py
scp ${sourcePath}/gui/BeaconUI.ui $piPath/gui/BeaconUI.ui
scp ${sourcePath}/gui/gui.py $piPath/gui/gui.py
scp ${sourcePath}/gui/qtres.py $piPath/gui/qtres.py
scp ${sourcePath}/beacon/hci.py $piPath/beacon/hci.py
scp ${sourcePath}/beacon/ibeacon.py $piPath/beacon/ibeacon.py
scp ${sourcePath}/comm/intmessage.py $piPath/comm/intmessage.py
scp ${sourcePath}/scanner/scannerble.py $piPath/scanner/scannerble.py
scp ${sourcePath}/utils/DBTools.py $piPath/utils/DBTools.py
scp ${sourcePath}/utils/debug.py $piPath/utils/debug.py
scp ${sourcePath}/getSysInfo.py $piPath/getSysInfo.py
