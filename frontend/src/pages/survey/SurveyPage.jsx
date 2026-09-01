import {
  useMemo,
  useState,
} from 'react'

import {
  BarChart3,
  CheckSquare,
  ChevronDown,
  Circle,
  ClipboardList,
  Copy,
  Eye,
  FilePlus2,
  GripVertical,
  Hash,
  Heading,
  ListChecks,
  Plus,
  RotateCcw,
  Save,
  SeparatorHorizontal,
  Trash2,
  Type,
} from 'lucide-react'

import AppShell
  from '../../components/AppShell'

import './SurveyPage.css'


// ==========================================================
// QUESTION TYPES
// ==========================================================

const QUESTION_TYPES = [

  {
    value: '',
    label: 'category',
    disabled: true,
  },

  {
    value: 'header',
    label: 'Header',
  },

  {
    value: 'short_text',
    label: 'Short Text',
  },

  {
    value: 'numeric',
    label: 'Numeric Answer',
  },

  {
    value: 'long_text',
    label: 'Long Text',
  },

  {
    value: 'single_choice',
    label: 'Single Choice',
  },

  {
    value: 'multiple_choice',
    label: 'Multiple Choice',
  },

  {
    value: 'single_choice_grid',
    label: 'Single Choice Grid',
  },

  {
    value: 'multiple_choice_grid',
    label: 'Multiple Choice Grid',
  },

  {
    value: 'linear_scale',
    label: 'Linear Scale',
  },

  {
    value: 'page_break',
    label: 'Page Break',
  },

]


// ==========================================================
// HELPERS
// ==========================================================

function createOption(
  text
) {

  return {
    id: crypto.randomUUID(),
    text,
  }
}


function createQuestion(
  number = 1,
  type = 'single_choice'
) {

  return {

    id: crypto.randomUUID(),

    title:
      type === 'header'
        ?
        'New Section'
        :
        type === 'page_break'
          ?
          'Page Break'
          :
          `Question ${number}`,

    description: '',

    type,

    required: false,

    allowOther: false,

    options: [
      createOption('Option 1'),
      createOption('Option 2'),
    ],

    gridRows: [
      createOption('Row 1'),
      createOption('Row 2'),
    ],

    gridColumns: [
      createOption('Column 1'),
      createOption('Column 2'),
      createOption('Column 3'),
    ],

    scaleMin: 1,

    scaleMax: 5,

    scaleMinLabel: 'Low',

    scaleMaxLabel: 'High',
  }
}


function createInitialSurvey() {

  return {

    title:
      'New SSAS Survey',

    description:
      '',

    questions: [
      createQuestion(
        1,
        'single_choice'
      ),
    ],
  }
}


// ==========================================================
// TOGGLE
// ==========================================================

function Toggle({
  checked,
  label,
  onChange,
}) {

  return (

    <label className="survey-toggle-row">

      <button
        type="button"

        className={
          checked
            ?
            'survey-toggle active'
            :
            'survey-toggle'
        }

        onClick={() =>
          onChange(
            !checked
          )
        }
      >

        <span />

      </button>


      <span>
        {label}
      </span>

    </label>

  )
}


// ==========================================================
// SIMPLE OPTION EDITOR
// ==========================================================

function OptionEditor({
  items,
  type,
  addLabel,
  onChange,
}) {

  const updateItem =
    (
      id,
      value
    ) => {

      onChange(
        items.map(
          (
            item
          ) =>
            item.id === id
              ?
              {
                ...item,
                text: value,
              }
              :
              item
        )
      )
    }


  const addItem =
    () => {

      onChange([
        ...items,

        createOption(
          `${
            addLabel
            ||
            'Option'
          } ${
            items.length + 1
          }`
        ),
      ])
    }


  const removeItem =
    (
      id
    ) => {

      if (
        items.length <= 1
      ) {
        return
      }


      onChange(
        items.filter(
          (
            item
          ) =>
            item.id !== id
        )
      )
    }


  return (

    <div className="survey-options">

      {
        items.map(
          (
            item,
            index
          ) => (

            <div
              className="survey-option-row"
              key={
                item.id
              }
            >

              {
                type === 'radio'
                  ?
                  <Circle size={20} />
                  :
                  type === 'checkbox'
                    ?
                    <CheckSquare size={20} />
                    :
                    <span className="survey-option-number">

                      {
                        index + 1
                      }

                    </span>
              }


              <input
                type="text"

                value={
                  item.text
                }

                onChange={
                  (
                    event
                  ) =>
                    updateItem(
                      item.id,
                      event.target.value
                    )
                }
              />


              <button
                type="button"

                disabled={
                  items.length <= 1
                }

                onClick={() =>
                  removeItem(
                    item.id
                  )
                }
              >

                <Trash2
                  size={17}
                />

              </button>

            </div>

          )
        )
      }


      <button
        type="button"

        className="survey-add-option"

        onClick={
          addItem
        }
      >

        <Plus
          size={17}
        />

        Add {
          addLabel
          ||
          'option'
        }

      </button>

    </div>

  )
}


// ==========================================================
// GRID EXAMPLE
// ==========================================================

function GridExample({
  question,
  multiple = false,
}) {

  return (

    <div className="survey-grid-example">

      <div className="survey-grid-example-table">

        <div className="survey-grid-corner" />


        {
          question
            .gridColumns
            .map(
              (
                column
              ) => (

                <div
                  key={
                    column.id
                  }

                  className="survey-grid-column-title"
                >

                  {
                    column.text
                  }

                </div>

              )
            )
        }


        {
          question
            .gridRows
            .flatMap(
              (
                row
              ) => [

                <div
                  key={
                    `${row.id}-label`
                  }

                  className="survey-grid-row-title"
                >

                  {
                    row.text
                  }

                </div>,

                ...question
                  .gridColumns
                  .map(
                    (
                      column
                    ) => (

                      <div
                        key={
                          `${row.id}-${column.id}`
                        }

                        className="survey-grid-choice-cell"
                      >

                        {
                          multiple
                            ?
                            (
                              <input
                                type="checkbox"
                                disabled
                              />
                            )
                            :
                            (
                              <input
                                type="radio"
                                disabled
                              />
                            )
                        }

                      </div>

                    )
                  ),

              ]
            )
        }

      </div>

    </div>

  )
}


// ==========================================================
// QUESTION EDITOR
// ==========================================================

function QuestionEditor({
  question,
  index,
  updateQuestion,
  deleteQuestion,
  duplicateQuestion,
}) {

  const isChoice =
    question.type ===
      'single_choice'
    ||
    question.type ===
      'multiple_choice'


  const isGrid =
    question.type ===
      'single_choice_grid'
    ||
    question.type ===
      'multiple_choice_grid'


  const isStructural =
    question.type ===
      'header'
    ||
    question.type ===
      'page_break'


  // ========================================================
  // HEADER
  // ========================================================

  if (
    question.type ===
    'header'
  ) {

    return (

      <article className="survey-structure-card survey-header-card">

        <div className="survey-structure-icon">

          <Heading
            size={24}
          />

        </div>


        <div className="survey-structure-content">

          <label>
            Heading / Section
          </label>


          <input
            type="text"

            value={
              question.title
            }

            onChange={
              (
                event
              ) =>
                updateQuestion({
                  title:
                    event.target.value,
                })
            }
          />


          <textarea
            rows="2"

            placeholder="Optional section description"

            value={
              question.description
            }

            onChange={
              (
                event
              ) =>
                updateQuestion({
                  description:
                    event.target.value,
                })
            }
          />

        </div>


        <button
          type="button"

          className="survey-structure-delete"

          onClick={
            deleteQuestion
          }
        >

          <Trash2
            size={18}
          />

        </button>

      </article>

    )
  }


  // ========================================================
  // PAGE BREAK
  // ========================================================

  if (
    question.type ===
    'page_break'
  ) {

    return (

      <article className="survey-structure-card survey-page-break-card">

        <SeparatorHorizontal
          size={26}
        />


        <div>

          <strong>
            Page Break
          </strong>

          <span>
            Questions below this point will appear on a new survey page.
          </span>

        </div>


        <button
          type="button"

          onClick={
            deleteQuestion
          }
        >

          <Trash2
            size={18}
          />

        </button>

      </article>

    )
  }


  return (

    <article className="survey-question-card">


      {/* ==================================================
          HANDLE
          ================================================== */}

      <div className="survey-question-handle">

        <GripVertical
          size={17}
        />

        <span>
          Question {
            index + 1
          }
        </span>

      </div>


      <div className="survey-question-layout">


        {/* =================================================
            LEFT EDITOR
            ================================================= */}

        <div className="survey-question-editor">


          <div className="survey-field">

            <label>
              Question
            </label>


            <input
              type="text"

              value={
                question.title
              }

              placeholder="Enter your question"

              onChange={
                (
                  event
                ) =>
                  updateQuestion({
                    title:
                      event.target.value,
                  })
              }
            />

          </div>


          <div className="survey-field">

            <label>

              Short information

              <span>
                optional
              </span>

            </label>


            <textarea
              rows="2"

              value={
                question.description
              }

              placeholder="Additional information for the respondent"

              onChange={
                (
                  event
                ) =>
                  updateQuestion({
                    description:
                      event.target.value,
                  })
              }
            />

          </div>


          {/* =================================================
              SHORT TEXT
              ================================================= */}

          {
            question.type ===
            'short_text'
            &&
            (

              <div className="survey-example-box">

                <span className="survey-example-label">
                  Example response
                </span>


                <input
                  type="text"

                  placeholder="Short answer"
                  disabled
                />

              </div>

            )
          }


          {/* =================================================
              NUMERIC
              ================================================= */}

          {
            question.type ===
            'numeric'
            &&
            (

              <div className="survey-example-box">

                <span className="survey-example-label">
                  Example numeric response
                </span>


                <div className="survey-numeric-example">

                  <Hash
                    size={18}
                  />

                  <input
                    type="number"

                    placeholder="0"

                    disabled
                  />

                </div>

              </div>

            )
          }


          {/* =================================================
              LONG TEXT
              ================================================= */}

          {
            question.type ===
            'long_text'
            &&
            (

              <div className="survey-example-box">

                <span className="survey-example-label">
                  Example response
                </span>


                <textarea
                  rows="4"

                  placeholder="Long text answer"

                  disabled
                />

              </div>

            )
          }


          {/* =================================================
              SINGLE / MULTIPLE CHOICE
              ================================================= */}

          {
            isChoice
            &&
            (

              <>

                <span className="survey-example-label">
                  Answer choices
                </span>


                <OptionEditor
                  items={
                    question.options
                  }

                  type={
                    question.type ===
                    'single_choice'
                      ?
                      'radio'
                      :
                      'checkbox'
                  }

                  addLabel="option"

                  onChange={
                    (
                      options
                    ) =>
                      updateQuestion({
                        options,
                      })
                  }
                />


                <div className="survey-choice-example">

                  <span>
                    Respondent example
                  </span>


                  {
                    question.options.map(
                      (
                        option
                      ) => (

                        <label
                          key={
                            option.id
                          }
                        >

                          <input
                            type={
                              question.type ===
                              'single_choice'
                                ?
                                'radio'
                                :
                                'checkbox'
                            }

                            disabled
                          />

                          {
                            option.text
                          }

                        </label>

                      )
                    )
                  }

                </div>

              </>

            )
          }


          {/* =================================================
              GRID QUESTIONS
              ================================================= */}

          {
            isGrid
            &&
            (

              <div className="survey-grid-editor">


                <div className="survey-grid-edit-column">

                  <h4>
                    Grid rows
                  </h4>


                  <OptionEditor
                    items={
                      question.gridRows
                    }

                    addLabel="row"

                    onChange={
                      (
                        gridRows
                      ) =>
                        updateQuestion({
                          gridRows,
                        })
                    }
                  />

                </div>


                <div className="survey-grid-edit-column">

                  <h4>
                    Grid columns
                  </h4>


                  <OptionEditor
                    items={
                      question.gridColumns
                    }

                    addLabel="column"

                    onChange={
                      (
                        gridColumns
                      ) =>
                        updateQuestion({
                          gridColumns,
                        })
                    }
                  />

                </div>


                <div className="survey-grid-live-example">

                  <span className="survey-example-label">
                    Grid example
                  </span>


                  <GridExample
                    question={
                      question
                    }

                    multiple={
                      question.type ===
                      'multiple_choice_grid'
                    }
                  />

                </div>


              </div>

            )
          }


          {/* =================================================
              LINEAR SCALE
              ================================================= */}

          {
            question.type ===
            'linear_scale'
            &&
            (

              <div className="survey-scale-editor">


                <div className="survey-scale-settings">


                  <div>

                    <label>
                      Minimum
                    </label>

                    <select
                      value={
                        question.scaleMin
                      }

                      onChange={
                        (
                          event
                        ) =>
                          updateQuestion({
                            scaleMin:
                              Number(
                                event.target.value
                              ),
                          })
                      }
                    >

                      <option value="0">
                        0
                      </option>

                      <option value="1">
                        1
                      </option>

                    </select>

                  </div>


                  <div>

                    <label>
                      Maximum
                    </label>

                    <select
                      value={
                        question.scaleMax
                      }

                      onChange={
                        (
                          event
                        ) =>
                          updateQuestion({
                            scaleMax:
                              Number(
                                event.target.value
                              ),
                          })
                      }
                    >

                      <option value="5">
                        5
                      </option>

                      <option value="7">
                        7
                      </option>

                      <option value="10">
                        10
                      </option>

                    </select>

                  </div>


                  <div>

                    <label>
                      Minimum label
                    </label>

                    <input
                      type="text"

                      value={
                        question.scaleMinLabel
                      }

                      onChange={
                        (
                          event
                        ) =>
                          updateQuestion({
                            scaleMinLabel:
                              event.target.value,
                          })
                      }
                    />

                  </div>


                  <div>

                    <label>
                      Maximum label
                    </label>

                    <input
                      type="text"

                      value={
                        question.scaleMaxLabel
                      }

                      onChange={
                        (
                          event
                        ) =>
                          updateQuestion({
                            scaleMaxLabel:
                              event.target.value,
                          })
                      }
                    />

                  </div>

                </div>


                <div className="survey-linear-example">

                  <span>
                    {
                      question.scaleMinLabel
                    }
                  </span>


                  {
                    Array.from({
                      length:
                        question.scaleMax
                        -
                        question.scaleMin
                        +
                        1,
                    }).map(
                      (
                        _,
                        offset
                      ) => {

                        const value =
                          question.scaleMin
                          +
                          offset


                        return (

                          <label
                            key={
                              value
                            }
                          >

                            <span>
                              {value}
                            </span>

                            <input
                              type="radio"

                              disabled
                            />

                          </label>

                        )
                      }
                    )
                  }


                  <span>
                    {
                      question.scaleMaxLabel
                    }
                  </span>

                </div>

              </div>

            )
          }


        </div>


        {/* =================================================
            SETTINGS
            ================================================= */}

        <aside className="survey-question-settings">


          <div className="survey-question-type">

            <label>
              Question type
            </label>


            <div className="survey-select-wrapper">

              <select
                value={
                  question.type
                }

                onChange={
                  (
                    event
                  ) =>
                    updateQuestion({
                      type:
                        event.target.value,
                    })
                }
              >

                {
                  QUESTION_TYPES.map(
                    (
                      item
                    ) => (

                      <option
                        key={
                          `${
                            item.value
                          }-${
                            item.label
                          }`
                        }

                        value={
                          item.value
                        }

                        disabled={
                          item.disabled
                        }
                      >

                        {
                          item.label
                        }

                      </option>

                    )
                  )
                }

              </select>


              <ChevronDown
                size={16}
              />

            </div>

          </div>


          {
            !isStructural
            &&
            (

              <Toggle
                checked={
                  question.required
                }

                label="Required field"

                onChange={
                  (
                    required
                  ) =>
                    updateQuestion({
                      required,
                    })
                }
              />

            )
          }


          {
            isChoice
            &&
            (

              <Toggle
                checked={
                  question.allowOther
                }

                label="Open text field"

                onChange={
                  (
                    allowOther
                  ) =>
                    updateQuestion({
                      allowOther,
                    })
                }
              />

            )
          }


          <div className="survey-question-actions">

            <button
              type="button"

              onClick={
                duplicateQuestion
              }
            >

              <Copy
                size={16}
              />

              Duplicate

            </button>


            <button
              type="button"

              className="danger"

              onClick={
                deleteQuestion
              }
            >

              <Trash2
                size={16}
              />

              Delete

            </button>

          </div>

        </aside>

      </div>

    </article>

  )
}


// ==========================================================
// PREVIEW
// ==========================================================

function SurveyPreview({
  survey,
}) {

  return (

    <section className="survey-preview">

      <div className="survey-preview-header">

        <span>
          SURVEY PREVIEW
        </span>


        <h2>
          {
            survey.title
            ||
            'Untitled Survey'
          }
        </h2>


        {
          survey.description
          &&
          (
            <p>
              {
                survey.description
              }
            </p>
          )
        }

      </div>


      {
        survey.questions.map(
          (
            question,
            index
          ) => {

            if (
              question.type ===
              'header'
            ) {

              return (

                <div
                  className="survey-preview-section-heading"

                  key={
                    question.id
                  }
                >

                  <h2>
                    {
                      question.title
                    }
                  </h2>


                  {
                    question.description
                    &&
                    (
                      <p>
                        {
                          question.description
                        }
                      </p>
                    )
                  }

                </div>

              )
            }


            if (
              question.type ===
              'page_break'
            ) {

              return (

                <div
                  className="survey-preview-page-break"

                  key={
                    question.id
                  }
                >

                  Page Break

                </div>

              )
            }


            return (

              <div
                key={
                  question.id
                }

                className="survey-preview-question"
              >

                <h3>

                  {
                    index + 1
                  }.

                  {' '}

                  {
                    question.title
                  }


                  {
                    question.required
                    &&
                    <span>*</span>
                  }

                </h3>


                {
                  question.description
                  &&
                  (
                    <p>
                      {
                        question.description
                      }
                    </p>
                  )
                }


                {
                  question.type ===
                  'short_text'
                  &&
                  (
                    <input
                      type="text"

                      placeholder="Your answer"
                    />
                  )
                }


                {
                  question.type ===
                  'numeric'
                  &&
                  (
                    <input
                      type="number"

                      placeholder="0"
                    />
                  )
                }


                {
                  question.type ===
                  'long_text'
                  &&
                  (
                    <textarea
                      rows="4"

                      placeholder="Your answer"
                    />
                  )
                }


                {
                  (
                    question.type ===
                    'single_choice'
                    ||
                    question.type ===
                    'multiple_choice'
                  )
                  &&
                  (

                    <div className="survey-preview-options">

                      {
                        question.options.map(
                          (
                            option
                          ) => (

                            <label
                              key={
                                option.id
                              }
                            >

                              <input
                                type={
                                  question.type ===
                                  'single_choice'
                                    ?
                                    'radio'
                                    :
                                    'checkbox'
                                }

                                name={
                                  question.id
                                }
                              />

                              {
                                option.text
                              }

                            </label>

                          )
                        )
                      }

                    </div>

                  )
                }


                {
                  question.type ===
                  'single_choice_grid'
                  &&
                  (

                    <GridExample
                      question={
                        question
                      }
                    />

                  )
                }


                {
                  question.type ===
                  'multiple_choice_grid'
                  &&
                  (

                    <GridExample
                      question={
                        question
                      }

                      multiple
                    />

                  )
                }


                {
                  question.type ===
                  'linear_scale'
                  &&
                  (

                    <div className="survey-linear-example">

                      <span>
                        {
                          question.scaleMinLabel
                        }
                      </span>


                      {
                        Array.from({
                          length:
                            question.scaleMax
                            -
                            question.scaleMin
                            +
                            1,
                        }).map(
                          (
                            _,
                            offset
                          ) => {

                            const value =
                              question.scaleMin
                              +
                              offset


                            return (

                              <label
                                key={
                                  value
                                }
                              >

                                <span>
                                  {
                                    value
                                  }
                                </span>

                                <input
                                  type="radio"

                                  name={
                                    question.id
                                  }
                                />

                              </label>

                            )
                          }
                        )
                      }


                      <span>
                        {
                          question.scaleMaxLabel
                        }
                      </span>

                    </div>

                  )
                }

              </div>

            )
          }
        )
      }


      <button
        type="button"

        className="survey-submit-preview"
      >

        Submit Survey

      </button>

    </section>

  )
}


// ==========================================================
// RESULTS
// ==========================================================

function SurveyResults() {

  return (

    <section className="survey-results">

      <ClipboardList
        size={43}
      />


      <h2>
        Survey Results
      </h2>


      <p>

        Responses will appear here
        after the survey has been
        published and respondents
        begin submitting answers.

      </p>


      <div className="survey-result-cards">

        <div>

          <strong>
            0
          </strong>

          <span>
            Responses
          </span>

        </div>


        <div>

          <strong>
            0%
          </strong>

          <span>
            Completion Rate
          </span>

        </div>


        <div>

          <strong>
            —
          </strong>

          <span>
            SSAS Dataset
          </span>

        </div>

      </div>

    </section>

  )
}


// ==========================================================
// INFORMATION SECTION
// ==========================================================

function SurveyInformation() {

  return (

    <section className="survey-online-information">

      <div className="survey-online-divider" />


      <h2>
        Create online survey
      </h2>


      <p>

        Create an online survey directly
        inside SSAS. First give your survey
        a name and description, then add the
        questions you want respondents to
        answer.

      </p>


      <p>
        You can choose between:
      </p>


      <ul>

        <li>
          Short Text
        </li>

        <li>
          Numeric Answer
        </li>

        <li>
          Long Text
        </li>

        <li>
          Single Choice
        </li>

        <li>
          Multiple Choice
        </li>

        <li>
          Single Choice Grid
        </li>

        <li>
          Multiple Choice Grid
        </li>

        <li>
          Linear Scale
        </li>

      </ul>


      <p>

        You can also create headings
        and sections to organize your
        questionnaire, or insert page
        breaks to divide a long survey
        into multiple pages.

      </p>


      <div className="survey-online-highlight">

        <ListChecks
          size={24}
        />


        <div>

          <strong>
            Designed for statistical analysis
          </strong>


          <span>

            Survey responses will later be
            convertible directly into an SSAS
            dataset so the collected data can
            be analyzed using the statistical
            analysis, visualization and report
            modules.

          </span>

        </div>

      </div>

    </section>

  )
}


// ==========================================================
// MAIN PAGE
// ==========================================================

export default function SurveyPage() {

  const [
    survey,
    setSurvey,
  ] =
    useState(
      createInitialSurvey
    )


  const [
    activeTab,
    setActiveTab,
  ] =
    useState(
      'create'
    )


  const [
    saved,
    setSaved,
  ] =
    useState(
      false
    )


  const questionCount =
    useMemo(
      () =>

        survey.questions.filter(
          (
            question
          ) =>
            question.type !==
              'header'
            &&
            question.type !==
              'page_break'
        ).length,

      [
        survey.questions,
      ]
    )


  // ========================================================
  // UPDATE ITEM
  // ========================================================

  const updateQuestion =
    (
      id,
      changes
    ) => {

      setSurvey(
        (
          current
        ) => ({

          ...current,

          questions:
            current.questions.map(
              (
                question
              ) =>
                question.id === id
                  ?
                  {
                    ...question,
                    ...changes,
                  }
                  :
                  question
            ),

        })
      )


      setSaved(
        false
      )
    }


  // ========================================================
  // ADD QUESTION
  // ========================================================

  const addQuestion =
    (
      type =
        'single_choice'
    ) => {

      setSurvey(
        (
          current
        ) => ({

          ...current,

          questions: [
            ...current.questions,

            createQuestion(
              current.questions.length
              +
              1,
              type
            ),
          ],

        })
      )


      setSaved(
        false
      )
    }


  // ========================================================
  // DELETE
  // ========================================================

  const deleteQuestion =
    (
      id
    ) => {

      setSurvey(
        (
          current
        ) => ({

          ...current,

          questions:
            current.questions.filter(
              (
                question
              ) =>
                question.id !== id
            ),

        })
      )


      setSaved(
        false
      )
    }


  // ========================================================
  // DUPLICATE
  // ========================================================

  const duplicateQuestion =
    (
      question
    ) => {

      const copy = {

        ...question,

        id:
          crypto.randomUUID(),

        title:
          `${question.title} (Copy)`,

        options:
          question.options.map(
            (
              option
            ) => ({
              ...option,
              id:
                crypto.randomUUID(),
            })
          ),

        gridRows:
          question.gridRows.map(
            (
              row
            ) => ({
              ...row,
              id:
                crypto.randomUUID(),
            })
          ),

        gridColumns:
          question.gridColumns.map(
            (
              column
            ) => ({
              ...column,
              id:
                crypto.randomUUID(),
            })
          ),
      }


      setSurvey(
        (
          current
        ) => {

          const index =
            current.questions.findIndex(
              (
                item
              ) =>
                item.id ===
                question.id
            )


          const questions = [
            ...current.questions,
          ]


          questions.splice(
            index + 1,
            0,
            copy
          )


          return {
            ...current,
            questions,
          }
        }
      )


      setSaved(
        false
      )
    }


  // ========================================================
  // NEW SURVEY
  // ========================================================

  const createNewSurvey =
    () => {

      const confirmed =
        window.confirm(
          'Create a new survey? Unsaved changes will be removed.'
        )


      if (
        !confirmed
      ) {
        return
      }


      setSurvey(
        createInitialSurvey()
      )


      setActiveTab(
        'create'
      )


      setSaved(
        false
      )
    }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <AppShell>

      <div className="survey-page">


        {/* ==================================================
            HEADER
            ================================================== */}

        <header className="survey-page-header">

          <div>

            <span className="survey-eyebrow">
              SURVEY BUILDER
            </span>


            <h1>
              Survey
            </h1>


            <p>

              Create questionnaires,
              collect responses and turn
              survey responses into
              statistical datasets.

            </p>

          </div>


          <div className="survey-question-count">

            <span>
              Questions
            </span>

            <strong>
              {
                questionCount
              }
            </strong>

          </div>

        </header>


        {/* ==================================================
            TOOLBAR
            ================================================== */}

        <section className="survey-toolbar">

          <div>

            <button
              type="button"

              className="survey-new-button"

              onClick={
                createNewSurvey
              }
            >

              <Plus
                size={18}
              />

              New Survey

            </button>


            <button
              type="button"

              className="survey-save-button"

              onClick={() =>
                setSaved(
                  true
                )
              }
            >

              <Save
                size={18}
              />

              {
                saved
                  ?
                  'Saved'
                  :
                  'Save Draft'
              }

            </button>

          </div>


          <div className="survey-save-status">

            <span>

              {
                saved
                  ?
                  'Draft saved'
                  :
                  'Unsaved changes'
              }

            </span>


            <button
              type="button"

              onClick={
                createNewSurvey
              }
            >

              <RotateCcw
                size={18}
              />

            </button>

          </div>

        </section>


        {/* ==================================================
            TABS
            ================================================== */}

        <nav className="survey-tabs">

          <button
            type="button"

            className={
              activeTab ===
              'create'
                ?
                'active'
                :
                ''
            }

            onClick={() =>
              setActiveTab(
                'create'
              )
            }
          >

            <FilePlus2
              size={17}
            />

            Create

          </button>


          <button
            type="button"

            className={
              activeTab ===
              'preview'
                ?
                'active'
                :
                ''
            }

            onClick={() =>
              setActiveTab(
                'preview'
              )
            }
          >

            <Eye
              size={17}
            />

            Preview & Publish

          </button>


          <button
            type="button"

            className={
              activeTab ===
              'results'
                ?
                'active'
                :
                ''
            }

            onClick={() =>
              setActiveTab(
                'results'
              )
            }
          >

            <BarChart3
              size={17}
            />

            Results

          </button>

        </nav>


        {/* ==================================================
            CREATE TAB
            ================================================== */}

        {
          activeTab ===
          'create'
          &&
          (

            <main>

              <section className="survey-information-card">

                <label>
                  Survey name
                </label>


                <input
                  type="text"

                  value={
                    survey.title
                  }

                  placeholder="Name of the survey"

                  onChange={
                    (
                      event
                    ) => {

                      setSurvey(
                        (
                          current
                        ) => ({
                          ...current,

                          title:
                            event.target.value,
                        })
                      )


                      setSaved(
                        false
                      )
                    }
                  }
                />


                <label>

                  Description

                  <span>
                    optional
                  </span>

                </label>


                <textarea
                  rows="3"

                  placeholder="Describe your survey"

                  value={
                    survey.description
                  }

                  onChange={
                    (
                      event
                    ) => {

                      setSurvey(
                        (
                          current
                        ) => ({
                          ...current,

                          description:
                            event.target.value,
                        })
                      )


                      setSaved(
                        false
                      )
                    }
                  }
                />

              </section>


              <section className="survey-question-list">

                {
                  survey.questions.map(
                    (
                      question,
                      index
                    ) => (

                      <QuestionEditor
                        key={
                          question.id
                        }

                        question={
                          question
                        }

                        index={
                          index
                        }

                        updateQuestion={
                          (
                            changes
                          ) =>
                            updateQuestion(
                              question.id,
                              changes
                            )
                        }

                        deleteQuestion={() =>
                          deleteQuestion(
                            question.id
                          )
                        }

                        duplicateQuestion={() =>
                          duplicateQuestion(
                            question
                          )
                        }
                      />

                    )
                  )
                }

              </section>


              {/* ============================================
                  ADD BUTTONS
                  ============================================ */}

              <section className="survey-add-content">

                <button
                  type="button"

                  onClick={() =>
                    addQuestion(
                      'single_choice'
                    )
                  }
                >

                  <Plus
                    size={18}
                  />

                  New Question

                </button>


                <button
                  type="button"

                  onClick={() =>
                    addQuestion(
                      'header'
                    )
                  }
                >

                  <Heading
                    size={18}
                  />

                  New Heading / New Section

                </button>


                <button
                  type="button"

                  onClick={() =>
                    addQuestion(
                      'page_break'
                    )
                  }
                >

                  <FilePlus2
                    size={18}
                  />

                  New Page

                </button>

              </section>


              {/* ============================================
                  INFORMATION BELOW SURVEY
                  ============================================ */}

              <SurveyInformation />

            </main>

          )
        }


        {/* ==================================================
            PREVIEW
            ================================================== */}

        {
          activeTab ===
          'preview'
          &&
          (

            <SurveyPreview
              survey={
                survey
              }
            />

          )
        }


        {/* ==================================================
            RESULTS
            ================================================== */}

        {
          activeTab ===
          'results'
          &&
          <SurveyResults />
        }

      </div>

    </AppShell>

  )
}
