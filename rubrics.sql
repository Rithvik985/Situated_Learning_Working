USE dissertation_data;

INSERT INTO dissertation_data.rubrics (name, dimensions)
VALUES (
    'Situated_Learning_rubric',
    JSON_ARRAY(

        -- 1. Conceptual Understanding and Application
        JSON_OBJECT(
            'name', 'Conceptual Understanding and Application',
            'criteria_output', JSON_OBJECT(
                'Identification of Relevant Concepts', 'Evaluate how accurately relevant academic concepts are identified in the workplace context.',
                'Depth of Application', 'Assess how effectively theoretical concepts are adapted and applied to real-world practice.',
                'Integration of Multiple Perspectives', 'Analyze the extent to which multiple theoretical or disciplinary perspectives are synthesized to form a comprehensive approach.'
            ),
            'score_explanation', JSON_OBJECT(
                'Score 4', JSON_OBJECT('Description', 'Demonstrates sophisticated engagement with theory, identifying multiple relevant concepts and applying them with nuance and critical integration.'),
                'Score 3', JSON_OBJECT('Description', 'Correctly identifies and applies relevant concepts with appropriate contextual adaptation.'),
                'Score 2', JSON_OBJECT('Description', 'Identifies some relevant concepts but applies them with limited depth or incomplete alignment to context.'),
                'Score 1', JSON_OBJECT('Description', 'Shows minimal or incorrect understanding of relevant concepts.')
            ),
            'criteria_explanation', 'This dimension evaluates how effectively academic theories and concepts are recognized, interpreted, and applied within a practical workplace scenario.'
        ),

        -- 2. Workplace Context Analysis
        JSON_OBJECT(
            'name', 'Workplace Context Analysis',
            'criteria_output', JSON_OBJECT(
                'Situational Assessment', 'Assess how clearly and comprehensively the workplace environment and scenario are described.',
                'Stakeholder Consideration', 'Evaluate the extent to which the needs and perspectives of relevant stakeholders are acknowledged.',
                'Organizational Constraints', 'Analyze how effectively practical limitations are recognized and addressed within the proposed approach.'
            ),
            'score_explanation', JSON_OBJECT(
                'Score 4', JSON_OBJECT('Description', 'Provides a rich and insightful analysis of the workplace environment, stakeholders, and constraints with precise contextual awareness.'),
                'Score 3', JSON_OBJECT('Description', 'Adequately explains workplace context with clear awareness of stakeholders and constraints.'),
                'Score 2', JSON_OBJECT('Description', 'Provides a basic overview of context with partial acknowledgment of stakeholders or limitations.'),
                'Score 1', JSON_OBJECT('Description', 'Lacks meaningful understanding of workplace context or fails to consider key stakeholders or constraints.')
            ),
            'criteria_explanation', 'This dimension assesses how well the learner understands and interprets the realities of the workplace scenario in which they are applying academic learning.'
        ),

        -- 3. Solution Development and Implementation
        JSON_OBJECT(
            'name', 'Solution Development and Implementation',
            'criteria_output', JSON_OBJECT(
                'Solution Viability', 'Evaluate the practicality and potential effectiveness of the proposed solution.',
                'Technical Accuracy', 'Assess the correctness and reliability of technical or procedural components.',
                'Resource Utilization', 'Analyze how efficiently available tools, personnel, or systems are leveraged.'
            ),
            'score_explanation', JSON_OBJECT(
                'Score 4', JSON_OBJECT('Description', 'Presents a well-designed, innovative, and feasible solution with clear implementation strategy and optimal resource usage.'),
                'Score 3', JSON_OBJECT('Description', 'Proposes a realistic and technically sound solution with basic implementation considerations.'),
                'Score 2', JSON_OBJECT('Description', 'Solution shows potential but lacks clarity or precision in technical or practical aspects.'),
                'Score 1', JSON_OBJECT('Description', 'Provides an impractical, incomplete, or technically flawed solution.')
            ),
            'criteria_explanation', 'This dimension evaluates the feasibility, accuracy, and practicality of the proposed approach to solving the workplace challenge.'
        ),

        -- 4. Critical Reflection and Learning
        JSON_OBJECT(
            'name', 'Critical Reflection and Learning',
            'criteria_output', JSON_OBJECT(
                'Self-Assessment', 'Evaluate the depth of personal reflection on strengths and limitations.',
                'Alternative Approaches', 'Assess consideration of different methodological or strategic options.',
                'Lessons for Future Application', 'Analyze how clearly transferable learning outcomes are articulated.'
            ),
            'score_explanation', JSON_OBJECT(
                'Score 4', JSON_OBJECT('Description', 'Demonstrates deep self-awareness with thoughtful evaluation of alternatives and clear articulation of future improvements.'),
                'Score 3', JSON_OBJECT('Description', 'Provides accurate reflection with reasonable insights into improvement.'),
                'Score 2', JSON_OBJECT('Description', 'Offers surface-level reflection with limited learning insights.'),
                'Score 1', JSON_OBJECT('Description', 'Shows minimal or no meaningful reflection.')
            ),
            'criteria_explanation', 'This dimension assesses the learner’s ability to critically evaluate their own process and derive growth-oriented insights.'
        ),

        -- 5. Communication and Documentation
        JSON_OBJECT(
            'name', 'Communication and Documentation',
            'criteria_output', JSON_OBJECT(
                'Clarity and Organization', 'Evaluate how well the response is structured and articulated.',
                'Technical Language', 'Assess the accuracy and appropriateness of domain-specific terminology.',
                'Supporting Evidence', 'Analyze the use of relevant data or references to justify claims.'
            ),
            'score_explanation', JSON_OBJECT(
                'Score 4', JSON_OBJECT('Description', 'Communicates with exceptional clarity, professional tone, and strong evidence integration.'),
                'Score 3', JSON_OBJECT('Description', 'Presents information clearly with generally appropriate terminology and supporting details.'),
                'Score 2', JSON_OBJECT('Description', 'Shows adequate clarity but with noticeable language or structural weaknesses.'),
                'Score 1', JSON_OBJECT('Description', 'Information is disorganized, unclear, or unsupported.')
            ),
            'criteria_explanation', 'This dimension evaluates how effectively the learner communicates their ideas and supports them with evidence.'
        ),

        -- 6. Professional Impact and Value
        JSON_OBJECT(
            'name', 'Professional Impact and Value',
            'criteria_output', JSON_OBJECT(
                'Workplace Value', 'Assess the tangible benefits or relevance of the solution to the workplace.',
                'Sustainability', 'Evaluate long-term feasibility and maintainability of the solution.',
                'Knowledge Transfer', 'Analyze the learner’s ability to translate academic knowledge into meaningful professional influence.'
            ),
            'score_explanation', JSON_OBJECT(
                'Score 4', JSON_OBJECT('Description', 'Demonstrates significant long-term value with clear potential for ongoing organizational or professional influence.'),
                'Score 3', JSON_OBJECT('Description', 'Provides clear workplace benefits with reasonable sustainability considerations.'),
                'Score 2', JSON_OBJECT('Description', 'Shows limited value or unclear sustainability.'),
                'Score 1', JSON_OBJECT('Description', 'Offers minimal or no meaningful professional impact.')
            ),
            'criteria_explanation', 'This dimension evaluates the real-world significance and longevity of the proposed solution within a professional environment.'
        )

    )
);
