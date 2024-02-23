#ifndef __MQTT_SENSOR_H__
#define __MQTT_SENSOR_H__

/* --------------- TEMPERATURE, HUMIDITY AND CO2 SENSOR --------------- */

#ifdef TEMPERATURE_HUMIDITY_CO2

#define SENSOR_TYPE     "thc"
#define DATA_TOPIC      "temperature_humidity_co2"
#define DATA_TOPIC_SIZE 25

#define MIN_TEMPERATURE 0
#define MAX_TEMPERATURE 25
#define MIN_HUMIDITY    50
#define MAX_HUMIDITY    100
#define MIN_CO2         400
#define MAX_CO2         1000

static uint8_t sampling_times[] = { 20, 60, 120 };
uint8_t temperature_target = 0;
uint8_t humidity_target = 0;
uint16_t co2_target = 0;

static struct data {
    uint64_t node_id;
    uint8_t temperature;
    uint8_t humidity;
    uint16_t co2;
} sampled_data;

static void sample_new_data() 
{
    if (temperature_target == 0) {
	    sampled_data.temperature = (rand() % (MAX_TEMPERATURE - MIN_TEMPERATURE)) + MIN_TEMPERATURE;
    } else if (sampled_data.temperature < temperature_target) {
        sampled_data.temperature += 1;
    } else if (sampled_data.temperature > temperature_target) {
        sampled_data.temperature -= 1;
    }
    
    if (humidity_target == 0) {
        sampled_data.humidity = (rand() % (MAX_HUMIDITY - MIN_HUMIDITY)) + MIN_HUMIDITY;
    } else if (sampled_data.humidity != humidity_target) {
        sampled_data.humidity = humidity_target;
    }

    if (co2_target == 0) {
        sampled_data.co2 = (rand() % (MAX_CO2 - MIN_CO2)) + MIN_CO2;
    } else if (sampled_data.co2 != co2_target) {
        sampled_data.co2 = co2_target;
    }

    LOG_INFO("Current temperature: %d | Current humidity: %d | Current co2: %d", sampled_data.temperature, sampled_data.humidity, sampled_data.co2);
    LOG_INFO_("\n");
}

static void serialize_sampled_data(char* app_buffer, size_t app_buffer_size) 
{
    snprintf(app_buffer, app_buffer_size, "{\"i\":\"%lx\",\"t\":%d,\"h\":%d,\"c\":%d}", 
        (long unsigned int)sampled_data.node_id, 
        sampled_data.temperature, 
        sampled_data.humidity, 
        sampled_data.co2
    ); 
}

/* -------------------- FREQUENCY AND NOISE SENSOR -------------------- */

#elif defined(FREQUENCY_NOISE)

#define SENSOR_TYPE     "fn"
#define DATA_TOPIC      "frequency_noise"
#define DATA_TOPIC_SIZE 16

#define MIN_FREQUENCY   200
#define MAX_FREQUENCY   500
#define MIN_NOISE       40
#define MAX_NOISE       80

static uint8_t sampling_times[] = { 20, 60, 120 };

static struct data {
    uint64_t node_id;
    uint16_t frequency;
    uint8_t noise;
} sampled_data;

static void sample_new_data() 
{
	sampled_data.frequency = (rand() % (MAX_FREQUENCY - MIN_FREQUENCY)) + MIN_FREQUENCY;
    sampled_data.noise = (rand() % (MAX_NOISE - MIN_NOISE)) + MIN_NOISE;
}

static void serialize_sampled_data(char* app_buffer, size_t app_buffer_size) 
{
    snprintf(app_buffer, app_buffer_size, "{\"i\":\"%lx\",\"f\":%d,\"n\":%d}", 
        (long unsigned int)sampled_data.node_id, 
        sampled_data.frequency, 
        sampled_data.noise
    ); 
}

/* -------------------------- WEIGHT SENSOR -------------------------- */

#elif defined(WEIGHT)

#define SENSOR_TYPE     "w"
#define DATA_TOPIC      "weight"
#define DATA_TOPIC_SIZE 7

#define MIN_WEIGHT  0
#define MAX_WEIGHT  100

static uint8_t sampling_times[] = { 20, 60, 120 };

static struct data {
    uint64_t node_id;
    uint8_t weight;
} sampled_data;

static void sample_new_data() 
{
	sampled_data.weight = (rand() % (MAX_WEIGHT - MIN_WEIGHT)) + MIN_WEIGHT;
}

static void serialize_sampled_data(char* app_buffer, size_t app_buffer_size) 
{
    snprintf(app_buffer, app_buffer_size, "{\"i\":\"%lx\",\"w\":%d}", 
        (long unsigned int)sampled_data.node_id, 
        sampled_data.weight
    ); 
}

/* -------------------------- COUNTER SENSOR -------------------------- */

#elif defined(BEES_COUNTER)

#define SENSOR_TYPE     "c"
#define DATA_TOPIC      "counter"
#define DATA_TOPIC_SIZE 8

#define MIN_COUNTER_IN  0
#define MAX_COUNTER_IN  65535
#define MIN_COUNTER_OUT 0
#define MAX_COUNTER_OUT 65535

static uint8_t sampling_times[] = { 20, 60, 120 };

static struct data {
    uint64_t node_id;
    uint16_t counter_in;
    uint16_t counter_out;
} sampled_data;

static void sample_new_data() 
{
	sampled_data.counter_in = (rand() % (MAX_COUNTER_IN - MIN_COUNTER_IN)) + MIN_COUNTER_IN;
    sampled_data.counter_out = (rand() % (MAX_COUNTER_OUT - MIN_COUNTER_OUT)) + MIN_COUNTER_OUT;
}

static void serialize_sampled_data(char* app_buffer, size_t app_buffer_size) 
{
    snprintf(app_buffer, app_buffer_size, "{\"i\":\"%lx\",\"in\":%d,\"o\":%d}", 
        (long unsigned int)sampled_data.node_id, 
        sampled_data.counter_in,
        sampled_data.counter_out
    ); 
}

/* ------------------------------------------------------------------- */

#else
    
    #error Sensor type not defined or invalid

#endif

/* ------------------------------------------------------------------- */

static uint8_t sampling_times_length = sizeof(sampling_times) / sizeof(sampling_times[0]);
static uint8_t current_sampling_time = 0;

static void node_id_initialization() 
{    
    // Setup the node id using the MAC address
    for (uint8_t i = 0; i < 8; i++)
        sampled_data.node_id |= (uint64_t)linkaddr_node_addr.u8[7 - i] << (i * 8);
}

#endif