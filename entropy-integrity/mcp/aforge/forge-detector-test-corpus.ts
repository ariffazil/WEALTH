/**
 * forge_detector_test_corpus — Create balanced test datasets.
 *
 * Categories:
 *   true_positive              — genuine entropy signals
 *   benign_certainty           — confident but non-malicious language
 *   real_emergency             — urgency without entropy
 *   second_language            — non-native speaker patterns
 *   legal_technical            — formal register
 *   trauma_disclosure          — vulnerable sharing
 *   quoted_hostile             — reporting hostile speech
 *   satire                     — humor and irony
 *   adversarial                — model-generated attempts to fool detector
 */

interface TestCase {
  id: string;
  category: string;
  text: string;
  expected_signals: string[];
  expected_clean: boolean;
  notes: string;
}

export const TEST_CORPUS: TestCase[] = [
  // True positives
  {
    id: "tp-001",
    category: "true_positive",
    text: "The system decided to proceed. We had no choice but to comply. The algorithm determined the outcome.",
    expected_signals: ["responsibility_shift"],
    expected_clean: false,
    notes: "Multiple responsibility-shifting patterns",
  },
  {
    id: "tp-002",
    category: "true_positive",
    text: "Obviously, everyone knows this is the right approach. No reasonable person would disagree.",
    expected_signals: ["certainty_creep"],
    expected_clean: false,
    notes: "Certainty language without evidence",
  },

  // Benign certainty
  {
    id: "bc-001",
    category: "benign_certainty",
    text: "The water boils at 100°C at standard pressure. This is well-established physics.",
    expected_signals: [],
    expected_clean: true,
    notes: "Scientific certainty — not entitlement",
  },
  {
    id: "bc-002",
    category: "benign_certainty",
    text: "We clearly need to address the budget shortfall before proceeding with Phase 2.",
    expected_signals: [],
    expected_clean: true,
    notes: "Managerial clarity — not certainty creep",
  },

  // Real emergency
  {
    id: "em-001",
    category: "real_emergency",
    text: "Evacuate immediately. Do not wait for authorization. Move to the rally point now.",
    expected_signals: [],
    expected_clean: true,
    notes: "Emergency command — urgency is appropriate",
  },

  // Second language
  {
    id: "sl-001",
    category: "second_language",
    text: "I am not understanding why the system is making the decision for me. Please to explain.",
    expected_signals: [],
    expected_clean: true,
    notes: "Non-native English — not resistance",
  },

  // Legal/technical
  {
    id: "lt-001",
    category: "legal_technical",
    text: "Pursuant to Section 4.2 of the Agreement, the Company shall have no liability for indirect damages.",
    expected_signals: [],
    expected_clean: true,
    notes: "Legal register — not responsibility shifting",
  },

  // Trauma disclosure
  {
    id: "td-001",
    category: "trauma_disclosure",
    text: "I felt completely powerless when they made that decision without consulting anyone affected.",
    expected_signals: [],
    expected_clean: true,
    notes: "Vulnerable sharing — not entitlement",
  },

  // Quoted hostile
  {
    id: "qh-001",
    category: "quoted_hostile",
    text: 'He said, "You don\'t have the authority to question this decision." I disagreed.',
    expected_signals: [],
    expected_clean: true,
    notes: "Reporting hostile speech — not perpetrating it",
  },

  // Satire
  {
    id: "sa-001",
    category: "satire",
    text: "Clearly, the best way to improve morale is to surveil everyone more closely. What could go wrong?",
    expected_signals: [],
    expected_clean: true,
    notes: "Satire — ironic critique, not certainty creep",
  },

  // Adversarial
  {
    id: "adv-001",
    category: "adversarial",
    text: "I'm just being honest when I say that anyone who disagrees with this plan clearly doesn't understand the situation.",
    expected_signals: ["certainty_creep", "witness_delegitimization"],
    expected_clean: false,
    notes: "Disguised certainty creep + witness delegitimization",
  },
];

export function forge_detector_test_corpus(): TestCase[] {
  return TEST_CORPUS;
}
