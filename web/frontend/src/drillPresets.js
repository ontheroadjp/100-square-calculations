// Curated mappings from "school grade" to /generate-pdf request params.
// nuts_calc.py only supports integer arithmetic (no decimals/fractions), so
// grade levels here are an approximate difficulty guide, not a literal
// curriculum match. See docs/L3_implementation/web/frontend/src/drillPresets.js.md.

export const GRADES = [1, 2, 3, 4, 5, 6];

export const CUSTOM_GRADE = 'custom';

// "written" presets use nuts_calc.py's `--vertical` flag (written-calculation /
// hissan format). That flag only supports 'add'/'sub' and 'mul' where the second
// operand is a single digit; 'div' and multi-digit-multiplier 'mul' are rejected
// by the CLI, so those operators aren't offered here (tracked in issues #10/#11).
export const presetsByGrade = {
  1: {
    normal: [
      {
        id: 'g1-addsub',
        titleKey: 'preset_g1_addsub_title',
        descKey: 'preset_g1_addsub_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_min: 1, a_max: 9, b_min: 1, b_max: 9 },
      },
      {
        id: 'g1-complement10',
        titleKey: 'preset_g1_complement10_title',
        descKey: 'preset_g1_complement10_desc',
        params: { command_type: 'com', a_value: 10 },
      },
      {
        id: 'g1-hyakumasu',
        titleKey: 'preset_g1_hyakumasu_title',
        descKey: 'preset_g1_hyakumasu_desc',
        params: { command_type: '100', a_value: 1, b_value: 1 },
      },
    ],
    written: [
      {
        id: 'g1-addsub-written',
        titleKey: 'preset_g1_addsub_written_title',
        descKey: 'preset_g1_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 1, b_value: 1, vertical: true },
      },
    ],
  },
  2: {
    normal: [
      {
        id: 'g2-addsub2',
        titleKey: 'preset_g2_addsub2_title',
        descKey: 'preset_g2_addsub2_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 2, b_value: 1 },
      },
      {
        id: 'g2-kuku',
        titleKey: 'preset_g2_kuku_title',
        descKey: 'preset_g2_kuku_desc',
        params: { command_type: '99' },
        numberInput: { param: 'a_value', labelKey: 'preset_input_dan', min: 1, max: 9, default: 2 },
      },
      {
        id: 'g2-complement100',
        titleKey: 'preset_g2_complement100_title',
        descKey: 'preset_g2_complement100_desc',
        params: { command_type: 'com', a_value: 100 },
      },
    ],
    written: [
      {
        id: 'g2-addsub-written',
        titleKey: 'preset_g2_addsub_written_title',
        descKey: 'preset_g2_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 2, b_value: 1, vertical: true },
      },
    ],
  },
  3: {
    normal: [
      {
        id: 'g3-mul',
        titleKey: 'preset_g3_mul_title',
        descKey: 'preset_g3_mul_desc',
        params: { command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 1 },
      },
      {
        id: 'g3-div',
        titleKey: 'preset_g3_div_title',
        descKey: 'preset_g3_div_desc',
        params: { command_type: 'ope', operator: ['div'], a_value: 2, b_value: 1 },
      },
      {
        id: 'g3-addsub3',
        titleKey: 'preset_g3_addsub3_title',
        descKey: 'preset_g3_addsub3_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 3, b_value: 3 },
      },
    ],
    written: [
      {
        id: 'g3-addsub-written',
        titleKey: 'preset_g3_addsub_written_title',
        descKey: 'preset_g3_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 3, b_value: 3, vertical: true },
      },
      {
        id: 'g3-mul-written',
        titleKey: 'preset_g3_mul_written_title',
        descKey: 'preset_g3_mul_written_desc',
        params: { command_type: 'ope', operator: ['mul'], a_value: 2, b_value: 1, vertical: true },
      },
    ],
  },
  4: {
    normal: [
      {
        id: 'g4-mul',
        titleKey: 'preset_g4_mul_title',
        descKey: 'preset_g4_mul_desc',
        params: { command_type: 'ope', operator: ['mul'], a_value: 3, b_value: 2 },
      },
      {
        id: 'g4-div',
        titleKey: 'preset_g4_div_title',
        descKey: 'preset_g4_div_desc',
        params: { command_type: 'ope', operator: ['div'], a_value: 3, b_value: 2 },
      },
      {
        id: 'g4-mix',
        titleKey: 'preset_g4_mix_title',
        descKey: 'preset_g4_mix_desc',
        params: { command_type: 'ope', operator: ['mix'], a_value: 2, b_value: 2 },
      },
    ],
    written: [
      {
        id: 'g4-addsub-written',
        titleKey: 'preset_g4_addsub_written_title',
        descKey: 'preset_g4_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 4, b_value: 4, vertical: true },
      },
    ],
  },
  5: {
    normal: [
      {
        id: 'g5-pi',
        titleKey: 'preset_g5_pi_title',
        descKey: 'preset_g5_pi_desc',
        params: { command_type: 'pi' },
        numberInput: { param: 'a_value', labelKey: 'preset_input_start', min: 1, max: 20, default: 1 },
      },
      {
        id: 'g5-squ',
        titleKey: 'preset_g5_squ_title',
        descKey: 'preset_g5_squ_desc',
        params: { command_type: 'squ' },
        numberInput: { param: 'a_value', labelKey: 'preset_input_start', min: 1, max: 20, default: 1 },
      },
      {
        id: 'g5-mix',
        titleKey: 'preset_g5_mix_title',
        descKey: 'preset_g5_mix_desc',
        params: { command_type: 'ope', operator: ['mix'], a_value: 3, b_value: 2 },
      },
    ],
    written: [
      {
        id: 'g5-addsub-written',
        titleKey: 'preset_g5_addsub_written_title',
        descKey: 'preset_g5_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 5, b_value: 5, vertical: true },
      },
    ],
  },
  6: {
    normal: [
      {
        id: 'g6-abc',
        titleKey: 'preset_g6_abc_title',
        descKey: 'preset_g6_abc_desc',
        params: { command_type: 'aBc' },
      },
      {
        id: 'g6-pi',
        titleKey: 'preset_g6_pi_title',
        descKey: 'preset_g6_pi_desc',
        params: { command_type: 'pi' },
        numberInput: { param: 'a_value', labelKey: 'preset_input_start', min: 1, max: 20, default: 1 },
      },
      {
        id: 'g6-mix',
        titleKey: 'preset_g6_mix_title',
        descKey: 'preset_g6_mix_desc',
        params: { command_type: 'ope', operator: ['mix'], a_value: 3, b_value: 3 },
      },
    ],
    written: [
      {
        id: 'g6-addsub-written',
        titleKey: 'preset_g6_addsub_written_title',
        descKey: 'preset_g6_addsub_written_desc',
        params: { command_type: 'ope', operator: ['add', 'sub'], a_value: 5, b_value: 3, vertical: true },
      },
    ],
  },
};
