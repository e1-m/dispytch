import {Writer} from "k6/x/kafka";
import {b64encode} from "k6/encoding";
import execution from "k6/execution";

const BROKERS = ["kafka:9092"];
const TOPIC = "my-load-test-topic";

export const options = {
    scenarios: {
        flood: {
            executor: "constant-arrival-rate",
            rate: 100,
            timeUnit: "1s",
            duration: "30s",
            preAllocatedVUs: 50,
            maxVUs: 200,
        },
    },
};

const writer = new Writer({
    brokers: BROKERS,
    topic: TOPIC,
    batchTimeout: 1000,
    batchSize: 50,
});

export default function () {
    const messages = [];
    const baseIter = execution.scenario.iterationInTest;

    for (let i = 0; i < 50; i++) {
        const payload = JSON.stringify({
            ts: Date.now(),
            id: `${baseIter}-${i}`,
            data: "flood"
        });

        messages.push({
            key: b64encode("test-key"),
            value: b64encode(payload),
        });
    }

    writer.produce({messages: messages});
}