#ifndef __COAP_ACTUATOR_H__
#define __COAP_ACTUATOR_H__

#include "string.h"

/* -------------------- TEMPERATURE ACTUATOR -------------------- */

#ifdef TEMPERATURE

#define SENSOR_TYPE "ta"

extern coap_resource_t res_temperature;

/* -------------------- VENTILATION ACTUATOR  -------------------- */

#elif defined(VENTILATION)

#define SENSOR_TYPE "va"

extern coap_resource_t res_ventilation;

/* --------------------------------------------------------------- */

#else
    
    #error Sensor type not defined or invalid

#endif

/* --------------------------------------------------------------- */

#define ACTUATOR_IP_SIZE    26
#define ACTUATOR_TYPE_SIZE  3

static uint8_t keepalive_periods[] = { 30, 60, 180 };
static uint8_t keepalive_periods_length = sizeof(keepalive_periods) / sizeof(keepalive_periods[0]);
static uint8_t current_keepalive = 0;

static struct actuator {
    uint64_t node_id;
    char ip[ACTUATOR_IP_SIZE];
    char type[ACTUATOR_TYPE_SIZE];
    uint8_t keepalive;
} actuator_info;

static void serialize_actuator_info(char* buffer, size_t buffer_size) 
{
    snprintf(buffer, buffer_size, "{\"i\":\"%lx\",\"ip\":\"%s\",\"t\":\"%s\",\"k\":%d}", 
        (long unsigned int)actuator_info.node_id, 
        actuator_info.ip, 
        actuator_info.type,
        actuator_info.keepalive
    );
}

static void serialize_keepalive(char* buffer, size_t buffer_size) 
{
    snprintf(buffer, buffer_size, "{\"i\":\"%lx\"}", 
        (long unsigned int)actuator_info.node_id
    ); 
}

static void node_ip_initilization()
{
    uint8_t state;

    // Get the unique local IP
    for (int i = 0; i < UIP_DS6_ADDR_NB; i++) {
        state = uip_ds6_if.addr_list[i].state;
        if (uip_ds6_if.addr_list[i].isused && (state == ADDR_TENTATIVE || state == ADDR_PREFERRED)) {
            if (uip_ds6_if.addr_list[i].ipaddr.u16[0] == 0xfd) {
                uiplib_ipaddr_snprint(actuator_info.ip, sizeof(actuator_info.ip), &uip_ds6_if.addr_list[i].ipaddr);
            }
        }
    }
}

static void node_info_initialization() 
{
    // Setup the node id using the MAC address
    for (uint8_t i = 0; i < 8; i++)
        actuator_info.node_id |= (uint64_t)linkaddr_node_addr.u8[7 - i] << (i * 8);
    
    static char type[] = SENSOR_TYPE;
    strcpy(actuator_info.type, type);
}

#endif