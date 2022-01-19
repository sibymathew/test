#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "../../../inc/bdaqctrl.h"
#include "../inc/compatibility.h"
using namespace Automation::BDaq;

typedef unsigned char byte;
#define  deviceDescription  L"USB-4761,BID#0"
const wchar_t* profilePath = L"../../profile/DemoDevice.xml";
int32    startPort = 0;
int32    portCount = 2;

inline void waitAnyKey()
{
   do{SLEEP(1);} while(!kbhit());
} 

int main(int argc, char* argv[])
{
   ErrorCode        ret = Success;
   InstantDiCtrl * instantDiCtrl = InstantDiCtrl::Create();
   do
   {
      DeviceInformation devInfo(deviceDescription);
      ret = instantDiCtrl->setSelectedDevice(devInfo);
      CHK_RESULT(ret);
      ret = instantDiCtrl->LoadProfile(profilePath);//Loads a profile to initialize the device.
      CHK_RESULT(ret);

      uint8  bufferForReading[64] = {0};//the first element of this array is used for start port
      do
      {
         ret = instantDiCtrl->Read(startPort, portCount, bufferForReading);
         CHK_RESULT(ret);  
         for ( int32 i = startPort;i < startPort+portCount; ++i)
         {
	    printf("%X", bufferForReading[i-startPort]);
         }
         SLEEP(1);
      }while(kbhit());
   }while(false);

	instantDiCtrl->Dispose();

   if(BioFailed(ret))
   {
      wchar_t enumString[256];
      AdxEnumToString(L"ErrorCode", (int32)ret, 256, enumString);
      printf("Some error occurred. And the last error code is 0x%X. [%ls]\n", ret, enumString);
      waitAnyKey();
   }
   return 0;
}
