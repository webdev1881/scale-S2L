#ifndef _LINUX_SDK_80_H_
#define _LINUX_SDK_80_H_

typedef enum
{
	E_ALIGN_LEFT = 0,
	E_ALIGN_CENTER = 1,
	E_ALIGN_RIGHT = 2
}EALIGN;

typedef enum
{
	E_FONT_A = 0x00,
	E_FONT_B = 0x01,
	E_CHAR_BOLD = 0x08,
	E_CHAR_TIMES_HIGH = 0x10,
	E_CHAR_DOUBLE_WIDTH = 0x20,
	E_CHAR_UNDERLINE = 0x80
}ECHARACTERFORMAT;

typedef enum
{
	E_CHARACTER_USA = 0,
	E_CHARACTER_FRANCE = 1,
	E_CHARACTER_GERMANY = 2,
	E_CHARACTER_BRITAIN = 3,
	E_CHARACTER_DENMARK_I = 4,
	E_CHARACTER_SWEDEN = 5,
	E_CHARACTER_ITALY = 6,
	E_CHARACTER_SPAIN_I = 7,
	E_CHARACTER_JAPAN = 8,
	E_CHARACTER_NORWAY = 9,
	E_CHARACTER_DENMARK_II = 10,
	E_CHARACTER_SPAIN_II = 11,
	E_CHARACTER_LATIN_AMERICA = 12,
	E_CHARACTER_KOREA = 13,
	E_CHARACTER_SLOVENIA = 14,
	E_CHARACTER_CHINA = 15
}ECHARACTER;

typedef enum
{
	E_UNDERLINE_CLOSE = 0,
	E_UNDERLINE_I = 1,
	E_UNDERLINE_II = 2
}EUNDERLINE;

typedef enum
{
	E_CODE_PAGE_CP437 = 0,
	E_CODE_PAGE_KATAKANA = 1,
	E_CODE_PAGE_CP850 = 2,
	E_CODE_PAGE_CP860 = 3,
	E_CODE_PAGE_CP863 = 4,
	E_CODE_PAGE_CP865 = 5,
	E_CODE_PAGE_WCP1252 = 16,
	E_CODE_PAGE_WCP1253 = 17,
	E_CODE_PAGE_CP852 = 18,
	E_CODE_PAGE_CP858 = 19	
}ECODEPAGE;

typedef enum
{
	E_CHAR_FONT_A = 0,
	E_CHAR_FONT_B = 1
	
}ECHARFONT;

typedef enum
{
	E_CHAR_HIGH_1 = 0x00,
	E_CHAR_HIGH_2 = 0x01,
	E_CHAR_HIGH_3 = 0x02,
	E_CHAR_HIGH_4 = 0x03,
	E_CHAR_HIGH_5 = 0x04,
	E_CHAR_HIGH_6 = 0x05,
	E_CHAR_HIGH_7 = 0x06,
	E_CHAR_HIGH_8 = 0x07
}ECHARHIGH;

typedef enum
{
	E_CHAR_WIDE_1 = 0x00,
	E_CHAR_WIDE_2 = 0x10,
	E_CHAR_WIDE_3 = 0x20,
	E_CHAR_WIDE_4 = 0x30,
	E_CHAR_WIDE_5 = 0x40,
	E_CHAR_WIDE_6 = 0x50,
	E_CHAR_WIDE_7 = 0x60,
	E_CHAR_WIDE_8 = 0x70
}ECHARWIDE;

typedef enum
{
	E_HRI_PRINT_COLSE = 0,
	E_HRI_PRINT_UPPER = 1,
	E_HRI_PRINT_BELOW = 2,
	E_HRI_PRINT_UPPER_AND_BELOW = 3	
}EHRIPRINTPOSITION;

typedef enum
{
	E_BAR_TYPE_UPC_A = 65,
	E_BAR_TYPE_UPC_E = 66,
	E_BAR_TYPE_JAN13 = 67,
	E_BAR_TYPE_JAN8 = 68,
	E_BAR_TYPE_CODE39 = 69,
	E_BAR_TYPE_ITF = 70,
	E_BAR_TYPE_CODABAR = 71,
	E_BAR_TYPE_CODE93 = 72,
	E_BAR_TYPE_CODE128 = 73	
}EBARTYPE;

typedef enum
{
	E_BAR_SIZE_AUTO = 0,
	E_BAR_SIZE_1 = 1,
	E_BAR_SIZE_2 = 2,
	E_BAR_SIZE_3 = 3,
	E_BAR_SIZE_4 = 4,
	E_BAR_SIZE_5 = 5,
	E_BAR_SIZE_6 = 6,
	E_BAR_SIZE_7 = 7,
	E_BAR_SIZE_8 = 8,
	E_BAR_SIZE_9 = 9,
	E_BAR_SIZE_10 = 10
}E2DBARSIZE;

typedef enum
{
	E_2DBAR_Check_Level_L = 0,
	E_2DBAR_Check_Level_M = 1,
	E_2DBAR_Check_Level_Q = 2,
	E_2DBAR_Check_Level_H = 3	
}E2DBARCHECKLEVEL;

typedef enum
{
	E_BAR_Component_1 = 1,
	E_BAR_Component_2 = 2,
	E_BAR_Component_3 = 3,
	E_BAR_Component_4 = 4,
	E_BAR_Component_5 = 5,
	E_BAR_Component_6 = 6,
	E_BAR_Component_7 = 7,
	E_BAR_Component_8 = 8	
}E2DBARCOMPONENT;

typedef enum
{
	E_CUTTING = 1,
	E_FEED_CUTTING = 66	
}ECUTTINGMODE;

typedef enum
{
	E_CHINESE_FORMAT_GBK = 0,
	E_CHINESE_FORMAT_UTF_8 = 1,	
	E_CHINESE_FORMAT_BIG5 = 3	
}ECHINESEFORMAT;

typedef enum
{
	E_PANEL_BUTTONS_ACTIVATION = 0,
	E_PANEL_BUTTONS_PROHIBIT = 1	
}EPANELBUTTONS;

typedef enum
{
	E_PRINTER_INFORMATION_ID_MODEL = 1,
	E_PRINTER_INFORMATION_ID_NUMBER = 2,	
	E_PRINTER_INFORMATION_HARDWARE_VERSION = 65,
	E_PRINTER_INFORMATION_MANUFACTURER = 66,	
	E_PRINTER_INFORMATION_PRINTER_NAME = 67,
	E_PRINTER_INFORMATION_COM_NAME = 68,
	E_PRINTER_INFORMATION_CHARACTER = 69
}EPRINTERINFORMATION;

typedef enum
{
	E_CUTTER_BOX_PIN2 = 0,
	E_CUTTER_BOX_PIN5 = 1	
}ECUTTERBOXPIN;

typedef enum
{
	E_PRINT_BITMAP_COMMON_MODE = 0,
	E_PRINT_BITMAP_DOUBLE_WIDTH = 1,
	E_PRINT_BITMAP_TIMES_HIGHER = 2,
	E_PRINT_BITMAP_FOURFOLD = 3
}EPRINTBITMAP;

typedef enum
{
	E_PRINT_DIRECTION_LEFT_TO_RIGHT = 0,
	E_PRINT_DIRECTION_BOTTOM_TO_TOP = 1,
	E_PRINT_DIRECTION_RIGHT_TO_LEFT = 2,
	E_PRINT_DIRECTION_TOP_TO_BOTTOM = 3
}EPRINTDIRECTION;

typedef enum
{
	E_TEST_PRINT_DUMP = 1,
	E_TEST_PRINT_PRINTER_STATE = 2,
	E_TEST_PRINT_ROLL_OF_PAPER = 3
}ETESTPRINT;

typedef struct _t_char_size 
{	
	ECHARHIGH high;
	ECHARWIDE wide;		
}char_size,*p_char_size;

typedef struct _t_bar_print 
{	
	EBARTYPE type;	
	char *data;	
}bar_print,*p_bar_print;

typedef struct _t_2dbar_print 
{	
	E2DBARSIZE size;
	E2DBARCHECKLEVEL level;
	E2DBARCOMPONENT component;
	char *data;	
}t2dbar_print,*p_t2dbar_print;

typedef struct _t_cutting_mode 
{	
	ECUTTINGMODE mode;
	unsigned int line;
}cutting_mode,*p_cutting_mode;

typedef struct _t_buzzer_set 
{	
	unsigned int times;
	unsigned int time;
}buzzer,*p_buzzer;

#define PRINTER_INFO_LEN 64

typedef struct _t_printer_information 
{	
	EPRINTERINFORMATION information;
	unsigned char receive[PRINTER_INFO_LEN];
}printer_information,*p_printer_information;

typedef struct _t_pulse_level_set 
{	
	ECUTTERBOXPIN pin;
	unsigned int time;
}pulse_level_set,*p_pulse_level_set;

typedef struct _t_pulse_time_set 
{	
	ECUTTERBOXPIN pin;
	unsigned int boottime;
	unsigned int offtime;
}pulse_time_set,*p_pulse_time_set;

typedef struct _t_page_print_area 
{	
	unsigned int x0;
	unsigned int y0;
	unsigned int wide;
	unsigned int high;
}page_print_area,*p_page_print_area;


unsigned int print_text(char * str);
unsigned int set_config_state(p_config_state pconfig);

/* ´òÓ¡Ö¸Áî */
unsigned int LF();
unsigned int CR();
unsigned int HT();
unsigned int set_feed_line(unsigned int line);
unsigned int set_feed_points(unsigned int points);
unsigned int set_level_location(unsigned int loation);
unsigned int set_printer_status(bool bset);
unsigned int self_test();

/* ¸ñÊ½ÉèÖÃ */
unsigned int set_line_spacing(unsigned int spacing);
unsigned int set_blank_amount(unsigned int amount);
unsigned int set_print_position(unsigned int position);
unsigned int set_print_area(unsigned int area);
unsigned int set_align_mode(EALIGN align);
unsigned int set_absolute_print_position(unsigned int position);
unsigned int defalt_line_spacing();

/* ×Ö·ûÉèÖÃ */
unsigned int set_character_format(unsigned int mode);
unsigned int set_inverse_mode(bool bset);
unsigned int set_rotate_mode(bool bset);
unsigned int select_chinese_mode(bool bset);
unsigned int set_overlap(bool bset);
unsigned int set_bold(bool bset);
unsigned int select_user_character(bool bset);
unsigned int set_resupinate_print(bool bset);
unsigned int set_charact(ECHARACTER character);
unsigned int set_under_line(EUNDERLINE underline);
unsigned int set_code_page(ECODEPAGE codepage);
unsigned int set_font(ECHARFONT font);
unsigned int set_char_size(p_char_size pcharsize);
unsigned int set_right_char_spacing(unsigned int spacing);
unsigned int cancel_user_char(unsigned int cancel);
unsigned int set_chinese_spacing(unsigned int left,unsigned int right);

/* ÌõÂëÉèÖÃ */
unsigned int hri_print_position(EHRIPRINTPOSITION eposition);
unsigned int set_bar_width(unsigned int wide);
unsigned int set_hri_font(ECHARFONT font);
unsigned int set_barcode_height(unsigned int high);
unsigned int set_bar_left_spacing(unsigned int spacing);
unsigned int print_bar(p_bar_print pbarprint);
unsigned int print_2dbar(p_t2dbar_print pt2dbar);

/* ¿ØÖÆÖ¸Áî */
unsigned int select_cutting_mode(p_cutting_mode pcutter);
unsigned int buzzer_set(p_buzzer pbuzzerset);
unsigned int set_chinese_format(ECHINESEFORMAT format);
unsigned int set_panel_button(EPANELBUTTONS set);
unsigned int full_cut();
unsigned int half_cut();

/* ×´Ì¬Ö¸Áî */
unsigned char * printer_state(unsigned char *receive);
unsigned char * paper_state(unsigned char *receive);
unsigned char * off_line_state(unsigned char *receive);
unsigned char * error_state(unsigned char *receive);
unsigned char * print_paper_state(unsigned char *receive);
unsigned char * get_printer_information(p_printer_information pinfo);
unsigned int error_recovery();
unsigned int clear_buffer();
unsigned int printer_initialization();
unsigned int send_pulse(p_pulse_level_set plevelset);
unsigned int send_pulse_time(p_pulse_time_set ptimeset);

/* Í¼ÐÎÉèÖÃ */
unsigned int print_raster_bmp(char * filename);
unsigned int download_bitmap(char *bitmap_name[],int count);
unsigned int print_nv_bitmap(int index);

/* Ò³Ä£Ê½ */
unsigned int page_mode();
unsigned int standard_mode();
unsigned int page_mode_print();
unsigned int print_and_standard();
unsigned int print_area(p_page_print_area parea);
unsigned int absolute_vertical_position(unsigned int position);
unsigned int relative_vertical_position(unsigned int position);
unsigned int print_direction(EPRINTDIRECTION direction);
unsigned int fourfold_chinese(bool bset);
unsigned int test_print(ETESTPRINT print);

#endif
