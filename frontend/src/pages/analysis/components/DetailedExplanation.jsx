import {
  AlertTriangle,
  Sparkles,
} from 'lucide-react'


export default function DetailedExplanation({
  explanation,
}) {
  // ========================================================
  // NOTHING TO DISPLAY
  // ========================================================

  if (!explanation) {
    return null
  }


  const sections =
    Array.isArray(
      explanation.sections
    )
      ? explanation.sections
      : []


  // ========================================================
  // RENDER
  // ========================================================

  return (
    <section className="detailed-explanation">

      {/* ==================================================
          HEADER
      ================================================== */}

      <div className="detailed-explanation-header">

        <div className="detailed-explanation-icon">

          <Sparkles
            size={18}
          />

        </div>


        <div>

          <span>
            SSAS EXPLANATION
          </span>


          <h3>
            {
              explanation.title ||
              'Detailed Statistical Explanation'
            }
          </h3>


          {explanation.introduction && (
            <p>
              {
                explanation
                  .introduction
              }
            </p>
          )}

        </div>

      </div>


      {/* ==================================================
          EXPLANATION SECTIONS
      ================================================== */}

      <div className="detailed-explanation-body">

        {sections.map(
          (
            section,
            sectionIndex
          ) => {

            const paragraphs =
              Array.isArray(
                section.paragraphs
              )
                ? section.paragraphs
                : []


            return (
              <article
                key={
                  `${
                    section.title ||
                    'section'
                  }-${sectionIndex}`
                }

                className="detailed-explanation-section"
              >

                <h4>
                  {
                    section.title ||
                    `Section ${
                      sectionIndex + 1
                    }`
                  }
                </h4>


                <div className="detailed-explanation-paragraphs">

                  {paragraphs.map(
                    (
                      paragraph,
                      paragraphIndex
                    ) => (

                      <p
                        key={
                          `${
                            sectionIndex
                          }-${
                            paragraphIndex
                          }`
                        }
                      >
                        {paragraph}
                      </p>

                    )
                  )}

                </div>

              </article>
            )
          }
        )}

      </div>


      {/* ==================================================
          STATISTICAL CAUTION
      ================================================== */}

      <div className="detailed-explanation-footer">

        <AlertTriangle
          size={15}
        />


        <p>
          Statistical results should
          be interpreted together with
          the research design, sample
          quality, measurement quality,
          assumptions, effect size and
          subject-matter knowledge.
        </p>

      </div>

    </section>
  )
}
