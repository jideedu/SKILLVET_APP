This page contain the source code of the web application for the SkillVet. SkillVet identifies relevant policy statements and assesses the traceability as complete, partial, or broken. SkillVet overcomes challenges in modelling privacy policies, such as contradictions like negations and statements related to multiple types of personal information.

Given a skill, SkillVet first identifies and classifies all statements in a privacy policy that relate to data practices over personal information. 
It then map each data statement with one or more Alexa permissions. These are the permissions the skill justifies in the privacy policy. 
We then compare these permissions with those the skill is authorised to request through the Amazon API during runtime. 
Depending on if the permissions requested match those found in the policy, the skill is then classified as having a Complete, Partial, or Broken privacy policy.
