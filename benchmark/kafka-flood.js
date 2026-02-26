import {Writer} from "k6/x/kafka";
import {b64encode} from "k6/encoding";
import execution from "k6/execution";

const brokers = ["kafka:9092"];
const topic = "benchmark_events";


const msgSize = parseInt(__ENV.K6_MESSAGE_SIZE_BYTES, 10);
const iteration_batch_size = parseInt(__ENV.ITERATION_BATCH_SIZE, 10);
const iteration_per_second = parseInt(__ENV.ITERATION_PER_SECOND, 10);
const duration = __ENV.DURATION;

export const options = {
    scenarios: {
        flood: {
            executor: "constant-arrival-rate",
            rate: iteration_per_second,
            timeUnit: "1s",
            duration: duration,
            preAllocatedVUs: 50,
            maxVUs: 200,
        },
    },
};

const writer = new Writer({
    brokers: brokers,
    topic: topic,
    batchTimeout: 1000,
    batchSize: iteration_batch_size,
});

export default function () {
    const messages = [];
    const baseIter = execution.scenario.iterationInTest;

    for (let i = 0; i < iteration_batch_size; i++) {
        const payload = JSON.stringify({
            id: `${baseIter}-${i}`,
            payload: "x".repeat(msgSize)
        });

        messages.push({
            key: b64encode("test-key"),
            value: b64encode(payload),
        });
    }

    writer.produce({messages: messages});
}