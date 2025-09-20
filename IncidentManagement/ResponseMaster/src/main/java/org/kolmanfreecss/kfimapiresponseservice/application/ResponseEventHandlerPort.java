package org.kolmanfreecss.kfimapiresponseservice.application;

import java.util.Collection;

import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.springframework.kafka.support.TopicPartitionOffset;
 

public interface ResponseEventHandlerPort {

    void rcvIncident(Collection<TopicPartitionOffset> response_ConsumerDetail);
}
