#ifndef __PROJECT_CONF_H__
#define __PROJECT_CONF_H__

#define LOG_CONF_LEVEL_MAIN LOG_LEVEL_INFO
#define UIP_CONF_TCP            1

#ifdef TEMPERATURE_HUMIDITY_CO2
#undef REST_MAX_CHUNK_SIZE
#define REST_MAX_CHUNK_SIZE     80
#endif

#endif
