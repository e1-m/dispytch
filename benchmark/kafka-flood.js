import {Writer} from "k6/x/kafka";
import {b64encode} from "k6/encoding";
import execution from "k6/execution";

const BROKERS = ["kafka:9092"];
const TOPIC = "benchmark_events";

const ITERATION_BATCH = 30000;
const ITERATION_PER_SECOND = 1;
const DURATION = "10s";

export const options = {
    scenarios: {
        flood: {
            executor: "constant-arrival-rate",
            rate: ITERATION_PER_SECOND,
            timeUnit: "1s",
            duration: DURATION,
            preAllocatedVUs: 50,
            maxVUs: 200,
        },
    },
};

const writer = new Writer({
    brokers: BROKERS,
    topic: TOPIC,
    batchTimeout: 1000,
    batchSize: ITERATION_BATCH,
});

export default function () {
    const messages = [];
    const baseIter = execution.scenario.iterationInTest;

    for (let i = 0; i < ITERATION_BATCH; i++) {
        const payload = JSON.stringify({
            id: `${baseIter}-${i}`,
            payload: "x".repeat(512)
        });

        messages.push({
            key: b64encode("test-key"),
            value: b64encode(payload),
        });
    }

    writer.produce({messages: messages});
}