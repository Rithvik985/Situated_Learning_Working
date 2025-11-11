#student.py

# @router.post("/analyze", response_model=SWOTAnalysis)
# async def analyze_submission(request: SWOTRequest, db: Session = Depends(get_db)):
#     """
#     Analyze student submission using SWOT analysis.
#     Students can request multiple analyses before final submission.
#     """
#     try:
#         # Get assignment details
#         assignment = db.query(DBGeneratedAssignment).filter(
#             DBGeneratedAssignment.id == request.assignment_id
#         ).first()
        
#         if not assignment:
#             raise HTTPException(status_code=404, detail="Assignment not found")

#         # Generate SWOT analysis using LLM
#         prompt = f"""
#         You are evaluating a student's submission for the following assignment:

#         Assignment Title: {assignment.title}
#         Assignment Description: {assignment.description}
#         Course: {assignment.course_name}

#         Analyze the student's submission using the SWOT framework, considering the assignment requirements and context.

#         1. Strengths: Identify key strong points where the submission effectively addresses the assignment requirements:
#            - Evaluate concept understanding
#            - Assess problem-solving approach
#            - Check alignment with assignment objectives
#            - Note effective use of course concepts

#         2. Weaknesses: Point out areas needing improvement:
#            - Identify missing assignment requirements
#            - Highlight conceptual misunderstandings
#            - Note structural or organizational issues
#            - Flag incomplete or superficial analysis

#         3. Opportunities: Suggest areas for growth and enhancement:
#            - Recommend ways to deepen analysis
#            - Identify potential for concept application
#            - Suggest additional perspectives to consider
#            - Point out learning opportunities

#         4. Threats: Identify potential risks or challenges:
#            - Flag potential misconceptions that could affect future work
#            - Identify gaps in understanding that need addressing
#            - Note any concerning patterns
#            - Highlight areas that could impact performance

#         5. Suggestions: Provide specific, actionable recommendations:
#            - Give clear steps for improvement
#            - Link suggestions to assignment requirements
#            - Provide concrete examples where possible
#            - Focus on achievable enhancements

#         Student Submission:
#         {request.content}

#         Provide a detailed, constructive analysis that helps the student improve their work while maintaining alignment with the assignment objectives.
#         Each point should be specific, actionable, and directly related to the assignment context.
#         """
        
#         # Initialize LLM client using the same config as evaluation service
#         if False:
#             client = OpenAI(api_key=llm_config.openai_api_key)
#         else:
#             vllm_base_url = llm_config.text_model_url.replace('/chat/completions', '')
#             client = OpenAI(base_url=vllm_base_url, api_key="EMPTY")

#         try:
#             # Call LLM with structured SWOT prompt
#             completion = await client.chat.completions.create(
#                 model=llm_config.text_model_name,
#                 messages=[
#                     {"role": "system", "content": "You are an expert academic evaluator performing SWOT analysis on student submissions."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.3,
#                 max_tokens=1500
#             )
            
#             # Parse the response to extract SWOT components
#             response_text = completion.choices[0].message.content.strip()
#             swot_components = {}
#             current_section = None
            
#             for line in response_text.split('\n'):
#                 line = line.strip()
#                 if line.lower().startswith('strengths:'):
#                     current_section = 'strengths'
#                     swot_components[current_section] = []
#                 elif line.lower().startswith('weaknesses:'):
#                     current_section = 'weaknesses'
#                     swot_components[current_section] = []
#                 elif line.lower().startswith('opportunities:'):
#                     current_section = 'opportunities'
#                     swot_components[current_section] = []
#                 elif line.lower().startswith('threats:'):
#                     current_section = 'threats'
#                     swot_components[current_section] = []
#                 elif line.lower().startswith('suggestions:'):
#                     current_section = 'suggestions'
#                     swot_components[current_section] = []
#                 elif line.startswith('-') and current_section:
#                     point = line[1:].strip()
#                     if point:
#                         swot_components[current_section].append(point)

#             # Create SWOT analysis object
#             swot_analysis = SWOTAnalysis(
#                 strengths=swot_components.get('strengths', []),
#                 weaknesses=swot_components.get('weaknesses', []),
#                 opportunities=swot_components.get('opportunities', []),
#                 threats=swot_components.get('threats', []),
#                 suggestions=swot_components.get('suggestions', [])
#             )

#         except Exception as e:
#             logger.error(f"Error in LLM SWOT analysis: {str(e)}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Failed to generate SWOT analysis: {str(e)}"
#             )
        
#         # Create or update submission record
#         submission = DBStudentSubmission(
#             id=str(uuid4()),
#             student_id=request.student_id,
#             assignment_id=request.assignment_id,
#             content=request.content,
#             evaluation_status="draft"
#         )
#         db.add(submission)
        
#         # Create SWOT analysis record
#         swot_result = DBStudentSWOT(
#             id=str(uuid4()),
#             submission_id=submission.id,
#             strengths=swot_analysis.strengths,
#             weaknesses=swot_analysis.weaknesses,
#             opportunities=swot_analysis.opportunities,
#             threats=swot_analysis.threats,
#             suggestions=swot_analysis.suggestions
#         )
#         db.add(swot_result)
#         db.commit()
        
#         return swot_analysis
        
#     except Exception as e:
#         logger.error(f"Error analyzing submission: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


