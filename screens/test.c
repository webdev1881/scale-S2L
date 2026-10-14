#include <errno.h>
#include <fcntl.h> 
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

#include "RT_def.h"
#include "RT_LinuxSDK80.h"

/* COM口测试 */
unsigned int test_by_com()
{
	unsigned char cmd[64] = {"asdfasdf13413413413409dsf98df7a9d8f7\r\n"};
	unsigned char receive[1] = {'\0'};
	unsigned char receive1[1] = {'\0'};
	char * bitmap[] = {
	"//home//zzf//Linux_SDK__//1.bmp",
	"//home//zzf//Linux_SDK__//1_2.bmp",
	"//home//zzf//Linux_SDK__//1_2_1_208.bmp",
	"//home//zzf//Linux_SDK__//2.bmp"
	};
	config_state config;
	int result = 0;
	bar_print pbarprint;	
	t2dbar_print pt2dbar;
	printer_information printinfo;

	pbarprint.type = E_BAR_TYPE_UPC_A;
	pbarprint.data = "12345678901";	
	
	pt2dbar.size = E_BAR_SIZE_AUTO;
	pt2dbar.level = E_2DBAR_Check_Level_L;
	pt2dbar.component = E_BAR_Component_8;
	pt2dbar.data = "123456";
	
	/* test serial port */
	config.eState = E_PORT_COM;
	strcpy(config.name,"/dev/ttyS0");
	config.context.baudrate = B19200;

	set_config_state(&config);	 /* 配置串口信息 */	
	
	self_test();
	set_feed_line(2);
	set_line_spacing(20);
	set_align_mode(E_ALIGN_CENTER);
	set_character_format(E_FONT_B|E_CHAR_BOLD|E_CHAR_TIMES_HIGH|E_CHAR_DOUBLE_WIDTH|E_CHAR_UNDERLINE);
	print_text("The is test print by com!");
	LF();	
	set_feed_line(2);
	
	set_character_format(E_FONT_A);
	print_text("The is test print by com!");
	LF();	
	set_feed_line(2);	
	
	set_inverse_mode(true);
	set_rotate_mode(true);
	set_resupinate_print(true);
	print_text("The is test print by com!");
	LF();	
	set_feed_line(2);	
	
	set_inverse_mode(false);
	set_rotate_mode(false);
	set_resupinate_print(false);
	print_text("The is test print by com!");
	LF();	
	set_feed_line(2);	
	
	set_bar_width(2);
	print_bar(&pbarprint);
	set_feed_line(2);	
	
	set_bar_width(3);
	hri_print_position(E_HRI_PRINT_UPPER);
	print_bar(&pbarprint);
	set_feed_line(2);	
	
	set_bar_width(4);
	hri_print_position(E_HRI_PRINT_BELOW);
	print_bar(&pbarprint);
	set_feed_line(2);
	
	set_bar_width(5);
	hri_print_position(E_HRI_PRINT_UPPER_AND_BELOW);
	print_bar(&pbarprint);
	set_feed_line(2);
		
	print_2dbar(&pt2dbar);
	set_feed_line(2);	
	
	printer_state(receive);	
	if(receive[0]&0x04)
	{		
		print_text("Cutter-box:open.");
		LF();
		set_feed_line(2);	
	}
	else
	{		
		print_text("Cutter-box:closed.");
		LF();
		set_feed_line(2);	
	}
	
	paper_state(receive1);
	if(receive1[0]&0x60)
	{		
		print_text("Paper:Run out of paper.");
		LF();
		set_feed_line(2);	
	}
	else
	{		
		print_text("Paper:Have paper.");
		LF();
		set_feed_line(2);	
	}
	
	printinfo.information = E_PRINTER_INFORMATION_ID_MODEL;	
	get_printer_information(&printinfo);
	
	if(printinfo.receive[0]&0x14)
	{
		print_text("ID Model:hexadecimal.");
		LF();
		set_feed_line(2);	
	}
	else if(printinfo.receive[0]&0x20)
	{
		print_text("ID Model:decimalism.");
		LF();
		set_feed_line(2);	
	}
	
	printinfo.information = E_PRINTER_INFORMATION_CHARACTER;	
	get_printer_information(&printinfo);
	print_text(printinfo.receive);
	LF();
	set_feed_line(4);
	
	printinfo.information = E_PRINTER_INFORMATION_MANUFACTURER;	
	get_printer_information(&printinfo);
	print_text(printinfo.receive);
	LF();
	set_feed_line(4);
	
	printinfo.information = E_PRINTER_INFORMATION_HARDWARE_VERSION;	
	get_printer_information(&printinfo);
	print_text(printinfo.receive);
	LF();
	set_feed_line(4);
	
	printinfo.information = E_PRINTER_INFORMATION_PRINTER_NAME;	
	get_printer_information(&printinfo);
	print_text(printinfo.receive);
	LF();
	set_feed_line(4);	
	
	print_raster_bmp("//home//zzf//Linux_SDK__//1_2.bmp"); /* 打印位图 */
	LF();
	set_feed_line(4);	
	
	download_bitmap(bitmap,4);    /* 下载位图 bitmap中存放4张位图的路径 */
	
	print_nv_bitmap(1);    /* 打印第一张位图 */
	LF();
	set_feed_line(4);
	
	print_nv_bitmap(2);	  /* 打印第二张位图 */
	LF();
	set_feed_line(4);
	
	print_nv_bitmap(3);	  /* 打印第三张位图 */
	LF();
	set_feed_line(4);
	
	print_nv_bitmap(4);    /* 打印第四张位图 */
	LF();
	set_feed_line(4);
	
	print_text("Test Print!");
	LF();
	set_feed_line(8);	
	full_cut();
}

/* USB口测试 */
unsigned int test_by_usb()
{		
	config_state config;
	bar_print pbarprint;	
	t2dbar_print pt2dbar;

	pbarprint.type = E_BAR_TYPE_UPC_A;
	pbarprint.data = "11223344556";	
	
	pt2dbar.size = E_BAR_SIZE_AUTO;
	pt2dbar.level = E_2DBAR_Check_Level_L;
	pt2dbar.component = E_BAR_Component_8;
	pt2dbar.data = "112233";
	
	config.eState = E_PORT_USB;
	strcpy(config.name,"/dev/usb/lp0");
	
	set_config_state(&config);

	set_feed_line(2);
	set_align_mode(E_ALIGN_CENTER);
	set_character_format(E_FONT_B|E_CHAR_BOLD|E_CHAR_TIMES_HIGH|E_CHAR_DOUBLE_WIDTH|E_CHAR_UNDERLINE);
	print_text("The is test print by usb!");
	LF();	
	set_feed_line(2);
		
	set_bar_width(2);
	print_bar(&pbarprint);
	set_feed_line(2);	
	
	print_2dbar(&pt2dbar);
	set_feed_line(2);	
	
	print_raster_bmp("//home//zzf//Linux_SDK__//2.bmp"); /* 打印位图 */
	LF();
	set_feed_line(8);	
	
	full_cut();
}

/* 网口测试 */
unsigned int test_by_enet()
{
	enet_info info = {0};
	config_state config;
	bar_print pbarprint;	
	t2dbar_print pt2dbar;

	pbarprint.type = E_BAR_TYPE_UPC_A;
	pbarprint.data = "55667788991";	
	
	pt2dbar.size = E_BAR_SIZE_AUTO;
	pt2dbar.level = E_2DBAR_Check_Level_L;
	pt2dbar.component = E_BAR_Component_8;
	pt2dbar.data = "445566";
	
	
	strcpy(info.ip,"192.168.1.33");
	info.portNumber = PRINTER_TCP_DEFAULT_PORT;
	
	config.eState = E_PORT_ENET;
	config.context.net_info = &info;
	
	set_config_state(&config);
	
	set_feed_line(2);
	set_line_spacing(20);
	set_align_mode(E_ALIGN_CENTER);
	set_character_format(E_FONT_B|E_CHAR_BOLD|E_CHAR_TIMES_HIGH|E_CHAR_DOUBLE_WIDTH|E_CHAR_UNDERLINE);
	print_text("The is test print by enet!");
	LF();	
	set_feed_line(2);
		
	set_bar_width(2);
	print_bar(&pbarprint);
	set_feed_line(2);	
	
	print_2dbar(&pt2dbar);
	set_feed_line(2);	
	
	print_raster_bmp("//home//zzf//Linux_SDK__//1.bmp"); /* 打印位图 */
	LF();
	set_feed_line(8);	
	
	full_cut();
}

int main(int argc,char **argv)
{	
	/* test com  */
	test_by_com();
	
	/* test usb */
	test_by_usb();
	
	/* test enet */
	test_by_enet();

	return 0;
}