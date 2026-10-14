/************************************************* 
Copyright: Xiamen Rongta Technology Co.Ltd.
Author: zhuzhengfeng
Date:2017-05-12
Description: common defines,maro,consts
**************************************************/ 

#ifndef _RT_COMMON_DEF_H_
#define _RT_COMMON_DEF_H_

typedef enum
{
	E_PORT_COM = 0,
	E_PORT_LPT = 1,
	E_PORT_ENET = 2,
	E_PORT_USB  = 3,
	E_PRINTER = 4
}E_CONFIG_STATE;

#ifndef MAX_PATH
#define MAX_PATH 260
#endif

typedef int bool;

#ifndef true
#define true 1
#endif

#ifndef false
#define false 0
#endif

#define PRINTER_TCP_DEFAULT_PORT 9100

#define NET_MAC_LEN 6
#define NET_IP_LEN 4
#define NET_SUBMASK_LEN 4
#define NET_GATEWAY_LEN 4

#define NET_INFO_LEN 64
#define NORMAL_LEN 128

/* error codes */
#define RT_ERR_SUCCESS 0x00

#define RT_ERR_INVALID_PARAM 0x01
#define RT_ERR_FILE_NOT_FIND 0x02

#define RT_ERR_OPEN_COM_PORT_FAIL 0x81
#define RT_ERR_SET_COM_FAIL 0x82
#define RT_ERR_SET_COM_NEED_CONFIG 0x83
#define RT_ERR_COM_WRITE_FAIL 0x84
#define RT_ERR_COM_READ_FAIL 0x85
#define RT_ERR_COM_GET_COMM_STATE_FAIL 0x86

#define RT_ERR_ENET_WRITE_FAIL 0x100
#define RT_ERR_ENET_READ_FAIL 0x101

#define RT_ERR_OPEN_LPT_PORT_FAIL 0x200
#define RT_ERR_LPT_WRITE_FAIL 0x201
#define RT_ERR_LPT_READ_FAIL 0x202
#define RT_ERR_LPT_CONFIG_FAIL 0x203

#define RT_ERR_OPEN_PRINTER_FAIL 0x300
#define RT_ERR_PRINTER_WRITE_FAIL 0x301
#define RT_ERR_PRINTER_READ_FAIL 0x302

#define RT_ERR_START_DOC_FAIL  0x400
#define RT_ERR_START_PAGE_FAIL 0x401
#define RT_ERR_END_PAGE_FAIL 0x402
#define RT_ERR_END_DOC_FAIL 0x403
#define RT_ERR_WRITE_PRINTER_LESS 0x404


#define RT_ERR_OPEN_USB_PORT_FAIL 0x500
#define RT_ERR_USB_WRITE_FAIL 0x501
#define RT_ERR_USB_READ_FAIL 0x502
#define RT_ERR_WRITE_USB_LESS 0x503

typedef struct  
{
	unsigned char mac[NET_INFO_LEN];
	char ip[NET_INFO_LEN];
	char subMask[NET_INFO_LEN];
	char gateWay[NET_INFO_LEN];
	unsigned short portNumber;
}enet_info,*p_enet_info;

typedef struct
{
	E_CONFIG_STATE eState;
	char name[MAX_PATH];
	union
	{
		p_enet_info net_info;
		int baudrate;
	}context;
}config_state,*p_config_state;

#endif