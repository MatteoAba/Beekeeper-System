CONTIKI_PROJECT = coap-actuator
all: $(CONTIKI_PROJECT)

CONTIKI = ../../../..

MODULES_REL += ./resources

include $(CONTIKI)/Makefile.dir-variables
MODULES += $(CONTIKI_NG_APP_LAYER_DIR)/coap
MODULES += $(CONTIKI_NG_LIB_DIR)/json

-include $(CONTIKI)/Makefile.identify-target

MODULES_REL += arch/platform/$(TARGET)

include $(CONTIKI)/Makefile.include