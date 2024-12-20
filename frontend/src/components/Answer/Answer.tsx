import { useMemo } from "react";
import { Stack, IconButton, Link } from "@fluentui/react";
import DOMPurify from "dompurify";

import styles from "./Answer.module.css";

import { ChatAppResponse } from "../../api";
import { parseAnswerToHtml } from "./AnswerParser";
import { AnswerIcon } from "./AnswerIcon";

interface Props {
    answer: ChatAppResponse;
    isSelected?: boolean;
    isStreaming: boolean;
    onCitationClicked: (filePath: string) => void;
    onThoughtProcessClicked: () => void;
    onSupportingContentClicked: () => void;
    onFollowupQuestionClicked?: (question: string) => void;
    showFollowupQuestions?: boolean;
}

export const Answer = ({
    answer,
    isSelected,
    isStreaming,
    onCitationClicked,
    onThoughtProcessClicked,
    onSupportingContentClicked,
    onFollowupQuestionClicked,
    showFollowupQuestions
}: Props) => {
    const followupQuestions = answer.choices[0].context.followup_questions;
    const messageContent = answer.choices[0].message.content;
    const parsedAnswer = useMemo(() => parseAnswerToHtml(messageContent, isStreaming, onCitationClicked), [answer]);
    const thoughts = answer.choices[0].context.thoughts.find((item)=>item.title==="Search results")?.description
    const seen_doc_ids = new Set<number>();
    const citations = thoughts ? thoughts.filter((element: Record<string, any>) => {
        if (!seen_doc_ids.has(element.doc_id)) {
            seen_doc_ids.add(element.doc_id);
            return true;
        }
        return false;
    }) : null;

    const sanitizedAnswerHtml = DOMPurify.sanitize(parsedAnswer.answerHtml);

    //console.log(JSON.stringify(citations))

    return (
        <Stack className={`${styles.answerContainer} ${isSelected && styles.selected}`} verticalAlign="space-between">
            {/* {
                JSON.stringify(thoughts)
            } */}
            {/* {
                thoughts.map((item)=>(
                    <div>{JSON.stringify(item)}</div>
                ))
            } */}

            <Stack.Item>
                <Stack horizontal horizontalAlign="space-between">
                    <AnswerIcon />
                    <div>
                        <IconButton
                            style={{ color: "black" }}
                            iconProps={{ iconName: "Lightbulb" }}
                            title="Show thought process"
                            ariaLabel="Show thought process"
                            onClick={() => onThoughtProcessClicked()}
                            disabled={!answer.choices[0].context.thoughts?.length}
                        />
                        <IconButton
                            style={{ color: "black" }}
                            iconProps={{ iconName: "ClipboardList" }}
                            title="Show supporting content"
                            ariaLabel="Show supporting content"
                            onClick={() => onSupportingContentClicked()}
                            disabled={!answer.choices[0].context.data_points}
                        />
                    </div>
                </Stack>
            </Stack.Item>

            <Stack.Item grow>
                <div className={styles.answerText} dangerouslySetInnerHTML={{ __html: sanitizedAnswerHtml }}></div>
            </Stack.Item>

            {/* {!!parsedAnswer.citations.length && (
                <Stack.Item>
                    <Stack horizontal wrap tokens={{ childrenGap: 5 }}>
                        <span className={styles.citationLearnMore}>Citations:</span>
                        {parsedAnswer.citations.map((x, i) => {
                            return (
                                <a key={i} className={styles.citation} title={x}>
                                    {`${++i}. ${x}`}
                                </a>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )} */}

            {citations && !!citations.length && (
                <Stack.Item>
                    <Stack wrap tokens={{ childrenGap: 5 }}>
                        <span className={styles.citationLearnMore}>Referenced Sources:</span>
                        {citations.map((x: Record<string, any>, i: number) => {
                            return (
                                // <>
                                // <a href={x.link} className={styles.citationLink} key={i} title={x.description} target="_blank">
                                //     <span className={styles.citationMarker}>{`${++i}.`}</span>
                                //     {x.name}
                                // </a>
                                // </>
                                <div>
                                    <span className={styles.citationMarker}>{`${++i}`}</span>
                                    <Link className={styles.citationLink} appearance="subtle" href={x.url} target="_blank">
                                        {x.title}
                                    </Link>
                                </div>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )}

            {!!followupQuestions?.length && showFollowupQuestions && onFollowupQuestionClicked && (
                <Stack.Item>
                    <Stack horizontal wrap className={`${!!parsedAnswer.citations.length ? styles.followupQuestionsList : ""}`} tokens={{ childrenGap: 6 }}>
                        <span className={styles.followupQuestionLearnMore}>Follow-up questions:</span>
                        {followupQuestions.map((x, i) => {
                            return (
                                <a key={i} className={styles.followupQuestion} title={x} onClick={() => onFollowupQuestionClicked(x)}>
                                    {`${x}`}
                                </a>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )}
        </Stack>
    );
};
