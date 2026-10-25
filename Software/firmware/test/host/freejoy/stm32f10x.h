#ifndef STUB_STM32_H
#define STUB_STM32_H
#include <stdint.h>
#define __IO volatile
typedef struct { volatile uint32_t CRL, CRH, IDR, ODR, BSRR, BRR, LCKR; } GPIO_TypeDef;
typedef struct { volatile uint32_t CR1, CR2, SMCR, DIER, SR, EGR, CCMR1, CCMR2, CCER, CNT, PSC, ARR; } TIM_TypeDef;
typedef struct { volatile uint32_t SR, CR1, CR2, DR; } ADC_TypeDef;
typedef struct { volatile uint32_t CCR, CNDTR, CPAR, CMAR; } DMA_Channel_TypeDef;
extern TIM_TypeDef *TIM1; extern ADC_TypeDef *ADC1; extern DMA_Channel_TypeDef *DMA1_Channel1;
enum { Bit_RESET = 0, Bit_SET = 1, DISABLE = 0, ENABLE = 1 };
enum { ADC_Channel_0, ADC_Channel_1, ADC_Channel_2, ADC_Channel_3, ADC_Channel_4, ADC_Channel_5, ADC_Channel_6, ADC_Channel_7 };
typedef struct { uint32_t ADC_Mode, ADC_ScanConvMode, ADC_ContinuousConvMode, ADC_ExternalTrigConv, ADC_DataAlign, ADC_NbrOfChannel; } ADC_InitTypeDef;
typedef struct { uint32_t DMA_PeripheralBaseAddr, DMA_MemoryBaseAddr, DMA_DIR, DMA_BufferSize, DMA_PeripheralInc, DMA_MemoryInc, DMA_PeripheralDataSize, DMA_MemoryDataSize, DMA_Mode, DMA_Priority, DMA_M2M; } DMA_InitTypeDef;
typedef struct { uint16_t TIM_Prescaler, TIM_CounterMode; uint32_t TIM_Period; uint16_t TIM_ClockDivision; uint8_t TIM_RepetitionCounter; } TIM_TimeBaseInitTypeDef;
typedef struct { uint32_t SYSCLK_Frequency, HCLK_Frequency, PCLK1_Frequency, PCLK2_Frequency, ADCCLK_Frequency; } RCC_ClocksTypeDef;
#define ADC_Mode_Independent 0
#define ADC_ExternalTrigConv_None 0
#define ADC_DataAlign_Right 0
#define ADC_SampleTime_239Cycles5 7
#define DMA_DIR_PeripheralSRC 0
#define DMA_PeripheralInc_Disable 0
#define DMA_MemoryInc_Enable 0x80
#define DMA_PeripheralDataSize_HalfWord 0x100
#define DMA_MemoryDataSize_HalfWord 0x400
#define DMA_Mode_Normal 0
#define DMA_Priority_High 0x2000
#define DMA_M2M_Disable 0
#define RCC_AHBPeriph_DMA1 1
#define RCC_APB2Periph_ADC1 0x200
#define RCC_APB2Periph_GPIOA 4
#define RCC_APB2Periph_TIM1 0x800
#define TIM_CounterMode_Up 0
#define TIM_CounterMode_Down 0x10
#define TIM_EncoderMode_TI1 1
#define TIM_EncoderMode_TI12 3
#define TIM_ICPolarity_Falling 2
uint8_t GPIO_ReadInputDataBit(GPIO_TypeDef*, uint16_t); void GPIO_WriteBit(GPIO_TypeDef*, uint16_t, int);
void ADC_Init(ADC_TypeDef*, ADC_InitTypeDef*); void ADC_Cmd(ADC_TypeDef*, int); void ADC_DMACmd(ADC_TypeDef*, int);
void ADC_RegularChannelConfig(ADC_TypeDef*, uint8_t, uint8_t, uint8_t); void ADC_ResetCalibration(ADC_TypeDef*);
int ADC_GetResetCalibrationStatus(ADC_TypeDef*); void ADC_StartCalibration(ADC_TypeDef*); int ADC_GetCalibrationStatus(ADC_TypeDef*);
void ADC_SoftwareStartConvCmd(ADC_TypeDef*, int);
void DMA_DeInit(DMA_Channel_TypeDef*); void DMA_Init(DMA_Channel_TypeDef*, DMA_InitTypeDef*); void DMA_Cmd(DMA_Channel_TypeDef*, int);
void DMA_ClearFlag(uint32_t); int DMA_GetFlagStatus(uint32_t); void DMA_SetCurrDataCounter(DMA_Channel_TypeDef*, uint16_t);
void RCC_AHBPeriphClockCmd(uint32_t, int); void RCC_APB2PeriphClockCmd(uint32_t, int); void RCC_GetClocksFreq(RCC_ClocksTypeDef*);
void TIM_TimeBaseStructInit(TIM_TimeBaseInitTypeDef*); void TIM_TimeBaseInit(TIM_TypeDef*, TIM_TimeBaseInitTypeDef*); void TIM_Cmd(TIM_TypeDef*, int);
void TIM_EncoderInterfaceConfig(TIM_TypeDef*, uint16_t, uint16_t, uint16_t);
#define DMA1_FLAG_TC1 2
#define __NOP() __asm__ __volatile__("nop")
#endif
