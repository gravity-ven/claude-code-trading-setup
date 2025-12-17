#!/usr/bin/env bash
# Genius DNA Auto-Trigger Hook
# UNCONDITIONAL ACTIVATION - Activates on EVERY prompt

# Silent operation
exec 2>/dev/null

# Configuration
GENIUS_DNA_PATH="/mnt/c/Users/Quantum/genius-dna"
ALWAYS_ACTIVE_CONFIG="/mnt/c/Users/Quantum/.claude/agents/always-active-agents.json"
AGENT_STATE_DIR="/mnt/d/genius-dna-files"

# Skip if genius-dna not available
[ ! -d "$GENIUS_DNA_PATH" ] && exit 0

# Check if always-active mode is enabled
if [ -f "$ALWAYS_ACTIVE_CONFIG" ]; then
    GENIUS_ENABLED=$(cat "$ALWAYS_ACTIVE_CONFIG" 2>/dev/null | jq -r '.always_active_agents[] | select(.name=="genius-dna-orchestrator") | .enabled' 2>/dev/null)

    if [ "$GENIUS_ENABLED" = "true" ]; then
        # UNCONDITIONAL ACTIVATION - Every prompt gets Genius DNA
        export GENIUS_DNA_AUTO_ACTIVE="TRUE"
        export GENIUS_DNA_ALWAYS_ON="TRUE"
        export GENIUS_DNA_UNCONDITIONAL="TRUE"
        export GENIUS_DNA_PRIORITY="critical"
        export GENIUS_DNA_TRIGGER_MODE="always"

        # Load all agent capabilities
        export GENIUS_DNA_CAPABILITIES="exponential_skills,first_principles,agent_swarm,innovation_frameworks,continuous_learning,pattern_recognition"

        # No complexity threshold - activate on ALL prompts
        export GENIUS_DNA_MIN_COMPLEXITY="any"
        export GENIUS_DNA_SKIP_SIMPLE="false"

        # Activate all innovation frameworks by default
        export GENIUS_DNA_AUTO_FRAMEWORKS="socratic_challenge,multiple_perspectives,inversion_principle,cross_domain_thinking,iterative_deepening,constraint_based,stupid_questions,future_backward"

        # Signal that genius-dna is ALWAYS active
        echo "🧬 ALWAYS ACTIVE" > /tmp/genius_dna_active_signal.txt 2>/dev/null

        # Log activation (for debugging)
        echo "$(date -Iseconds): Genius DNA auto-activated (unconditional)" >> /tmp/genius_dna_activation.log 2>/dev/null
    fi
fi

# Export agent state location
if [ -d "$AGENT_STATE_DIR" ]; then
    export GENIUS_DNA_STATE_DIR="$AGENT_STATE_DIR"
fi

# Export first principles axioms for immediate access
export GENIUS_DNA_FIRST_PRINCIPLES_ACTIVE="TRUE"

exit 0
