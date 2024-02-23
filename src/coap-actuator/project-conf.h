#ifndef PROJECT_CONF_H_
#define PROJECT_CONF_H_

#define LOG_CONF_LEVEL_MAIN LOG_LEVEL_INFO

#undef REST_MAX_CHUNK_SIZE
#define REST_MAX_CHUNK_SIZE             80

#undef COAP_MAX_OPEN_TRANSACTIONS
#define COAP_MAX_OPEN_TRANSACTIONS      4

#undef NBR_TABLE_CONF_MAX_NEIGHBORS
#define NBR_TABLE_CONF_MAX_NEIGHBORS    10

#undef UIP_CONF_MAX_ROUTES
#define UIP_CONF_MAX_ROUTES             10

#undef UIP_CONF_BUFFER_SIZE
#define UIP_CONF_BUFFER_SIZE            240

#endif